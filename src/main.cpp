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

void ERCMain()
{
	LCD.Clear();
	LCD.WriteLine("Waiting for touch.");

    int x, y;
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

        //NS LIGHT GREEN, WALK LIGHT ON
        red1.Write(false);
        dontWalk1.Write(false);
		green1.Write(true);
        walk1.Write(true);
		Sleep(5);
        //NS WALK LIGHT OFF
        walk1.Write(false);
        dontWalk1.Write(true);
        Sleep(2);
        //NS LIGHT YELLOW
        yellow1.Write(true);
		green1.Write(false);
        Sleep(2);
        //NS LIGHT RED
        yellow1.Write(false);
		red1.Write(true);
        Sleep(1);

		// East-West CYCLE

        //NS LIGHT GREEN, WALK LIGHT ON
        red2.Write(false);
        dontWalk2.Write(false);
		green2.Write(true);
        walk2.Write(true);
		Sleep(5);
        //NS WALK LIGHT OFF
        walk2.Write(false);
        dontWalk2.Write(true);
        Sleep(2);
        //NS LIGHT YELLOW
        yellow2.Write(true);
		green2.Write(false);
        Sleep(2);
        //NS LIGHT RED
        yellow2.Write(false);
		red2.Write(true);
        Sleep(1);
	}
}