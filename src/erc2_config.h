/*
 * erc2_config.h -- turning parts of the ERC2 library off to get RAM back.
 *
 * The Mega has 8 KB of SRAM, and a full build of the library spends about
 * 4.9 KB of it before your ERCMain() runs. Most of that is the link: the
 * buffers that let ERC2 Link show your logs, browse the SD card and mirror the
 * LCD, over the cable and over Bluetooth.
 *
 * That is worth paying for, because a robot you cannot see inside is a robot
 * you debug by guessing. But if your program has run out of room, turning off
 * something it never uses is a better trade than shrinking your own arrays.
 *
 * To switch something off, delete the // in front of its #define. To get it
 * back, put the // back. Nothing here is permanent, and a fresh project has
 * everything on.
 *
 * Every build prints what is switched off, so check the [ERC2-CONFIG] lines in
 * the build output if a feature seems to have gone missing.
 *
 * This file is yours. It lives in src/ because the template replaces its own
 * files when the library updates, and src/ is the part it never touches.
 */

#ifndef ERC2_CONFIG_H
#define ERC2_CONFIG_H


/* ---------------------------------------------------------------------------
 * Bluetooth                                                frees ~990 bytes
 *
 * ERC2 Link reaches the board over the cable OR over Bluetooth. This turns off
 * the radio half only; plugging in the USB cable still works exactly as
 * before. Worth knowing: Bluetooth is how you watch a robot during a run,
 * when there is no cable attached to watch it through.
 * ------------------------------------------------------------------------ */

// Bluetooth is disabled by default
#define ERC2_DISABLE_BLUETOOTH


/* ---------------------------------------------------------------------------
 * The LCD mirror                                            frees ~200 bytes
 *
 * Showing the LCD on your computer in ERC2 Link. The screen on the board is
 * unaffected -- this is only the copy sent to the PC. A small saving in RAM,
 * but about 1.6 KB of program space, which is the one to reach for if you are
 * short on flash rather than SRAM.
 * ------------------------------------------------------------------------ */

// #define ERC2_DISABLE_LCD_MIRROR


/* ---------------------------------------------------------------------------
 * The SD card                                                frees ~780 bytes
 *
 * SD, File, and the file browser in ERC2 Link. Also frees about 20 KB of
 * program space, which is the largest single saving here.
 *
 * Unlike the others, this one shows up as a compile error rather than a
 * missing feature: if your program still calls SD.FOpen() or declares a
 * File, it will not build until you remove that code or this line. That is
 * deliberate -- quietly doing nothing with a student's data file would be
 * worse.
 * ------------------------------------------------------------------------ */

// #define ERC2_DISABLE_SD


/* ---------------------------------------------------------------------------
 * All of ERC2 Link                                         frees ~2,160 bytes
 *
 * The big one, and the one to be sure about. This removes the link entirely:
 * no logs in ERC2 Link, no file browser, no LCD mirror, over the cable or over
 * Bluetooth. ERC2 Link will not connect to the board at all, and the only way
 * back is to comment this line out and re-upload.
 *
 * Serial itself still works -- Serial.print() and the Arduino serial monitor
 * are unaffected, and in fact the port is entirely yours in this build.
 * ------------------------------------------------------------------------ */

// #define ERC2_DISABLE_LINK

/*
 * Not switchable: RCS, RPS and the ESP32 link. The course sends the kill
 * signal over that link, and a robot that cannot be stopped by the course is
 * not one that may run on it. Turning Bluetooth off above leaves all of that
 * working -- it is a separate radio on the same chip.
 */

#endif // ERC2_CONFIG_H
