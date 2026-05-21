from smbus2 import SMBus
import time


class LSM303AGR:
    # I2C 7-bit addresses (tipici): ACC 0x19, MAG 0x1E
    ACC_ADDR = 0x19
    MAG_ADDR = 0x1E

    # --- Accelerometer (LIS2DH-like) registers ---
    WHO_AM_I_A   = 0x0F
    CTRL_REG1_A  = 0x20
    CTRL_REG4_A  = 0x23
    OUT_X_L_A    = 0x28  # auto-increment via bit 0x80 in I2C

    # --- Magnetometer (LSM303AGR) registers ---
    WHO_AM_I_M   = 0x4F
    CFG_REG_A_M  = 0x60
    CFG_REG_B_M  = 0x61
    CFG_REG_C_M  = 0x62
    OUTX_L_REG_M = 0x68  # X_L..Z_H = 0x68..0x6D

    def __init__(self, bus: int = 1, acc_addr: int = None, mag_addr: int = None):
        self.bus = SMBus(bus)
        if acc_addr is not None:
            self.ACC_ADDR = acc_addr
        if mag_addr is not None:
            self.MAG_ADDR = mag_addr

        self._init_acc()
        self._init_mag()

    @staticmethod
    def _int16(lo: int, hi: int) -> int:
        v = (hi << 8) | lo
        return v - 65536 if v & 0x8000 else v

    def _read_block(self, addr: int, start_reg: int, n: int) -> bytes:
        # read_i2c_block_data ritorna list[int]
        data = self.bus.read_i2c_block_data(addr, start_reg, n)
        return bytes(data)

    # --------- INIT ---------
    def _init_acc(self):
        # 100 Hz, enable X/Y/Z (0b0101_0111)
        self.bus.write_byte_data(self.ACC_ADDR, self.CTRL_REG1_A, 0x57)
        # BDU=1 (bit7) + HR=1 (bit3) => 0b1000_1000
        self.bus.write_byte_data(self.ACC_ADDR, self.CTRL_REG4_A, 0x88)

    def _init_mag(self):
        # CFG_REG_A_M (0x60): [7]=COMP_TEMP_EN (deve stare a 1), [3:2]=ODR, [1:0]=MD
        # Imposto: temp compensation ON, ODR=10Hz (00), continuous mode MD=00
        self.bus.write_byte_data(self.MAG_ADDR, self.CFG_REG_A_M, 0x80)

        # CFG_REG_B_M: lascio default (offset canc / LPF off)
        self.bus.write_byte_data(self.MAG_ADDR, self.CFG_REG_B_M, 0x00)

        # CFG_REG_C_M: BDU=1 (bit4) utile per letture coerenti (datasheet: CFG_REG_C_M)
        self.bus.write_byte_data(self.MAG_ADDR, self.CFG_REG_C_M, 0x10)

    # --------- READ ---------
    def read_acc_raw(self):
        # auto-increment: OR 0x80 sul registro di partenza
        d = self._read_block(self.ACC_ADDR, self.OUT_X_L_A | 0x80, 6)
        x = self._int16(d[0], d[1])
        y = self._int16(d[2], d[3])
        z = self._int16(d[4], d[5])
        return x, y, z

    def read_mag_raw(self):
        # OUTX_L_REG_M..OUTZ_H_REG_M = 6 bytes
        d = self._read_block(self.MAG_ADDR, self.OUTX_L_REG_M, 6)
        x = self._int16(d[0], d[1])
        y = self._int16(d[2], d[3])
        z = self._int16(d[4], d[5])
        return x, y, z
    
    @staticmethod
    def mag_raw_to_uT(mx, my, mz):
        """
        Convert raw magnetometer values to microtesla (µT)
        LSM303AGR sensitivity: 1.5 mG/LSB = 0.15 µT/LSB
        """
        SCALE = 0.15  # µT per LSB
        return (
            mx * SCALE,
            my * SCALE,
            mz * SCALE
        )
    
    def close(self):
        self.bus.close()




if __name__ == "__main__":
    lsm = LSM303AGR()

    try:
        while True:
            ax, ay, az = lsm.read_acc_raw()
            mx, my, mz = lsm.read_mag_raw()

            print(f"ACC  x:{ax:6d} y:{ay:6d} z:{az:6d}")
            print(f"MAG  x:{mx:6d} y:{my:6d} z:{mz:6d}")
            mx_uT, my_uT, mz_uT = lsm.mag_raw_to_uT(mx, my, mz)

            print(f"MAG [µT]  X:{mx_uT:7.2f}  Y:{my_uT:7.2f}  Z:{mz_uT:7.2f}")
            
            print("-" * 30)

            time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        lsm.close()