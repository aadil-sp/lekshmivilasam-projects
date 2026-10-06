/*
 * RoboNav-SLAM: High-Speed RPLiDAR C1/S2/A-Series JSON Stream Bridge
 * Zero-sleep tight loop — runs at full sensor rate (~10 Hz scans)
 * Outputs to /tmp/lidar_scan.json atomically (rename trick, no partial reads)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <math.h>
#include <signal.h>
#include <time.h>
#include "sl_lidar.h"
#include "sl_lidar_driver.h"

using namespace sl;

static volatile bool ctrl_c_pressed = false;
void ctrlc(int) { ctrl_c_pressed = true; }

int main(int argc, const char * argv[]) {
    const char * port    = (argc > 1) ? argv[1] : "/dev/ttyUSB0";
    sl_u32       baud    = (argc > 2) ? (sl_u32)atoi(argv[2]) : 460800;

    signal(SIGINT,  ctrlc);
    signal(SIGTERM, ctrlc);

    printf("[*] RoboNav LiDAR Bridge — %s @ %u baud\n", port, baud);

    ILidarDriver * drv = *createLidarDriver();
    if (!drv) { fprintf(stderr, "[!] createLidarDriver failed\n"); return -1; }

    // Try provided baud then fallback list
    sl_u32 bauds[] = { baud, 460800, 256000, 115200 };
    IChannel * channel = nullptr;
    bool connected = false;
    for (int bi = 0; bi < 4 && !connected; bi++) {
        if (channel) delete channel;
        channel = *createSerialPortChannel(port, bauds[bi]);
        if (SL_IS_OK(drv->connect(channel))) {
            baud = bauds[bi];
            connected = true;
        }
    }
    if (!connected) {
        fprintf(stderr, "[!] Cannot connect to LiDAR at %s\n", port);
        delete drv; delete channel; return -1;
    }

    sl_lidar_response_device_info_t devinfo;
    if (SL_IS_OK(drv->getDeviceInfo(devinfo))) {
        printf("[+] Model: %d  FW: %d.%02d  HW: %d  Baud: %u\n",
               devinfo.model,
               devinfo.firmware_version >> 8,
               devinfo.firmware_version & 0xFF,
               devinfo.hardware_version, baud);
    }

    sl_lidar_response_device_health_t health;
    if (SL_IS_OK(drv->getHealth(health)) && health.status != SL_LIDAR_STATUS_OK) {
        fprintf(stderr, "[!] LiDAR health error: %d, resetting...\n", health.status);
        drv->reset();
        usleep(2000000);
    } else {
        // Force reset anyway to clear stuck state from hard kills
        drv->reset();
        usleep(1500000);
    }

    // Start motor at default speed
    drv->setMotorSpeed();
    usleep(500000); // 500 ms motor spin-up

    // Use startScan with force=false, use_typical=true for best-matching mode
    sl_result ans = drv->startScan(false, true);
    if (SL_IS_FAIL(ans)) {
        fprintf(stderr, "[!] startScan failed: %x\n", (unsigned)ans);
        delete drv; delete channel; return -1;
    }

    printf("[+] Scanning — writing /tmp/lidar_scan.json\n");

    static sl_lidar_response_measurement_node_hq_t nodes[8192];
    const char * tmp_file   = "/tmp/lidar_scan_tmp.json";
    const char * final_file = "/tmp/lidar_scan.json";

    long scan_count = 0;
    struct timespec t_last; clock_gettime(CLOCK_MONOTONIC, &t_last);

    while (!ctrl_c_pressed) {
        size_t count = sizeof(nodes) / sizeof(nodes[0]);
        // grabScanDataHq blocks until a full 360° scan is ready (~100ms at 10Hz)
        ans = drv->grabScanDataHq(nodes, count);
        if (!SL_IS_OK(ans)) continue;

        drv->ascendScanData(nodes, count);

        // Compute Hz
        scan_count++;
        struct timespec t_now; clock_gettime(CLOCK_MONOTONIC, &t_now);
        double elapsed = (t_now.tv_sec - t_last.tv_sec) +
                         (t_now.tv_nsec - t_last.tv_nsec) * 1e-9;
        float hz = (elapsed > 0) ? (float)(scan_count / elapsed) : 0;

        FILE * fp = fopen(tmp_file, "w");
        if (!fp) continue;

        fprintf(fp, "{\"status\":\"ONLINE\",\"model\":%d,\"hz\":%.1f,\"count\":%zu,\"points\":[",
                devinfo.model, hz, count);

        bool first = true;
        for (size_t i = 0; i < count; i++) {
            float angle_deg = nodes[i].angle_z_q14 * 90.f / 16384.f;
            float dist_mm   = nodes[i].dist_mm_q2 / 4.0f;
            int   quality   = nodes[i].quality >> SL_LIDAR_RESP_MEASUREMENT_QUALITY_SHIFT;
            if (dist_mm > 10.0f && quality > 0) {
                float rad = angle_deg * ((float)M_PI / 180.f);
                if (!first) fputc(',', fp);
                // Compact format: smaller JSON for faster network transfer
                fprintf(fp, "[%.1f,%.0f]", angle_deg, dist_mm);
                first = false;
            }
        }
        fprintf(fp, "]}\n");
        fclose(fp);
        rename(tmp_file, final_file); // atomic on Linux

        // Print Hz every 5 seconds
        if (elapsed > 5.0) {
            printf("[~] Scan rate: %.1f Hz  Points: %zu\n", hz, count);
            scan_count = 0;
            clock_gettime(CLOCK_MONOTONIC, &t_last);
        }
    }

    printf("\n[*] Stopping LiDAR...\n");
    drv->stop();
    drv->setMotorSpeed(0);
    delete drv;
    delete channel;
    printf("[+] Done.\n");
    return 0;
}
