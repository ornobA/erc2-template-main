//BONUSES DONE: DOUBLE RED, BLINKING DON'T WALK, PEDESTRIAN BUZZER.

#include <Arduino.h>
#include <erc2.h>

using namespace erc2;

DigitalOutput green1(Pin0);
DigitalOutput yellow1(Pin1);
DigitalOutput red1(Pin2);
DigitalOutput dontWalk1(Pin3);
DigitalOutput walk1(Pin4);

DigitalOutput green2(Pin8);
DigitalOutput yellow2(Pin9);
DigitalOutput red2(Pin10);
DigitalOutput dontWalk2(Pin11);
DigitalOutput walk2(Pin12);

DigitalOutput buzz(Pin6);
// DigitalOutput buzz2(Pin14); 

DigitalOutput button1(Pin5);
DigitalOutput button2(Pin13);

void ERCMain()
{
    LCD.Clear();
    LCD.WriteLine("Waiting for touch.");

    int x, y, i = 0, j = 0;
    while (!LCD.Touch(&x, &y))
    {
    }
    while (!LCD.Touch(&x, &y))
    {
    }

    LCD.WriteLine("Starting!");

    while (true)
    {

        // North-South CYCLE

        // GREEN LIGHT, START WALKING
        red1.Write(false);
        dontWalk1.Write(false);
        green1.Write(true);
        walk1.Write(true);

        //BUZZ CYCLE

        i = 0;
        j = 0;

        while (j < 19)
        {
            i = 0;
            while (i <= 249)
            {
                buzz.Toggle();
                SleepMs(1);
                i++;
            }
        SleepMs(250);
        j++;
        }

        //Sleep(5);

        // STOP WALKING
        walk1.Write(false);
        dontWalk1.Write(true);

        // BLINKING DONT WALK
        dontWalk1.Write(true);
        Sleep(0.5);
        dontWalk1.Write(false);
        Sleep(0.5);
        dontWalk1.Write(true);
        Sleep(0.5);
        dontWalk1.Write(false);
        Sleep(0.5);

        // YELLOW LIGHT
        yellow1.Write(true);
        green1.Write(false);
        Sleep(2);
        // RED LIGHT
        yellow1.Write(false);
        red1.Write(true);

        // DOUBLE RED BONUS
        Sleep(1);

        // East-West CYCLE

        // GREEN LIGHT, START WALKING
        red2.Write(false);
        dontWalk2.Write(false);
        green2.Write(true);
        walk2.Write(true);

        //BUZZ CYCLE

        i = 0;
        j = 0;

        while (j < 19)
        {
            i = 0;
            while (i <= 249)
            {
                buzz.Toggle();
                SleepMs(1);
                i++;
            }
        SleepMs(250);
        j++;
        }

        // STOP WALKING
        walk2.Write(false);
        dontWalk2.Write(true);

        // BLINKING DONT WALK
        dontWalk2.Write(true);
        Sleep(0.5);
        dontWalk2.Write(false);
        Sleep(0.5);
        dontWalk2.Write(true);
        Sleep(0.5);
        dontWalk2.Write(false);
        Sleep(0.5);

        // YELLOW LIGHT
        yellow2.Write(true);
        green2.Write(false);
        Sleep(2);
        // RED LIGHT
        yellow2.Write(false);
        red2.Write(true);

        // DOUBLE RED BONUS
        Sleep(1);
    }
}