#pragma once
// Application console on separate header GPIOs; not the USB/boot UART pins.
// Electrical interface qualification is still required. Never connect adapter VCC.
#if defined(ARDUINO_USB_CDC_ON_BOOT) && ARDUINO_USB_CDC_ON_BOOT
#error "Rev A bench console requires UART0, not USB CDC; disable CDC on boot."
#endif
constexpr int CONSOLE_RX = 17;
constexpr int CONSOLE_TX = 18;
constexpr unsigned CONSOLE_BAUD = 460800;
