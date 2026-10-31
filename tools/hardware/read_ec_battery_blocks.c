/* Read-only Dell Venue 5055 EC battery blocks, derived from BIOS A04 DSDT.
 * Only transaction: one command/address byte followed by 18 received bytes.
 * No data writes, Control subcommands, resets, unseal, EEPROM or scanning.
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <linux/i2c.h>
#include <linux/i2c-dev.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>

static uint8_t crc8(const uint8_t *p, size_t n) {
    uint8_t crc = 0;
    for (size_t i=0;i<n;i++) {
        crc ^= p[i];
        for (int j=0;j<8;j++) crc = (uint8_t)((crc & 0x80) ? (crc<<1)^7 : crc<<1);
    }
    return crc;
}
static unsigned word(const uint8_t *p) { return p[0] | ((unsigned)p[1]<<8); }
static int identity(const char *file, const char *expected) {
    FILE *f=fopen(file,"r"); char buffer[128]={0};
    if(!f)return 0;
    if(!fgets(buffer,sizeof(buffer),f)){fclose(f);return 0;}
    fclose(f); buffer[strcspn(buffer,"\r\n")]=0;
    return strcmp(buffer,expected)==0;
}
int main(int argc, char **argv) {
    if (argc != 1) { fprintf(stderr,"Usage: %s (fixed, audited EC read only)\n",argv[0]); return 2; }
    if(!identity("/sys/class/dmi/id/product_name","Venue 10 Pro 5055") ||
       !identity("/sys/class/dmi/id/board_name","084N67") ||
       !identity("/sys/class/dmi/id/bios_version","A04")) {
        fprintf(stderr,"Refusing: audited for Venue 5055 board 084N67 BIOS A04 only\n");return 2;
    }
    FILE *f=fopen("/sys/bus/i2c/devices/i2c-0/firmware_node/path","r");
    char path[128]={0};
    if (!f || !fgets(path,sizeof(path),f) || !strstr(path,"\\_SB_.I2C1")) {
        fprintf(stderr,"Refusing: adapter ACPI identity is not I2C1\n"); if(f)fclose(f); return 2;
    }
    fclose(f);
    int fd=open("/dev/i2c-0",O_RDWR|O_CLOEXEC);
    if (fd<0) {perror("open");return 1;}
    /* Never I2C_SLAVE_FORCE. Refuse if a kernel client owns the address. */
    if(ioctl(fd,I2C_SLAVE,0x10)<0){perror("I2C_SLAVE");close(fd);return 1;}
    const uint8_t commands[]={0xa2,0xa3};
    for(size_t i=0;i<sizeof(commands);i++) {
        uint8_t cmd=commands[i], data[18]={0};
        struct i2c_msg messages[2]={
            {.addr=0x10,.flags=0,.len=1,.buf=&cmd},
            {.addr=0x10,.flags=I2C_M_RD,.len=sizeof(data),.buf=data}};
        struct i2c_rdwr_ioctl_data transaction={.msgs=messages,.nmsgs=2};
        if(ioctl(fd,I2C_RDWR,&transaction)!=2){perror("I2C_RDWR");close(fd);return 1;}
        uint8_t packet[20]={0x20,cmd,0x21};
        memcpy(packet+3,data,17);
        uint8_t expected=crc8(packet,sizeof(packet));
        printf("command=0x%02x raw=",cmd);
        for(size_t j=0;j<sizeof(data);j++)printf("%02x",data[j]);
        printf(" length=%u crc_received=0x%02x crc_expected=0x%02x\n",data[0],data[17],expected);
        if(data[0]!=16 || expected!=data[17]){
            fprintf(stderr,"Refusing to interpret unverified EC response\n");close(fd);return 1;
        }
        const uint8_t *p=data+1;
        if(cmd==0xa2)printf("status=0x%04x current_raw=%u remaining_mAh=%u voltage_mV=%u\n",word(p),word(p+2),word(p+4),word(p+6));
        else printf("power_unit_raw=0x%04x design_capacity_mAh=%u full_capacity_mAh=%u design_voltage_mV=%u cycles=%u serial_raw=%u\n",word(p),word(p+2),word(p+4),word(p+6),word(p+10),word(p+12));
        fflush(stdout);
        struct timespec pause={.tv_sec=0,.tv_nsec=600000000};
        nanosleep(&pause,NULL);
    }
    close(fd);return 0;
}
