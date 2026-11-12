// TODO: Import all necessary ERC2 libraries here
#include <Arduino.h>
#include <erc2.h>
#define SLEEP 1.0

using namespace erc2;

// TODO: Fill in the pin declarations
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

	XXXX; // TODO: Declare variables
	while (XXXX)
	{
		// TODO: Screen is not being touched
	}
	while (XXXX)
	{
		// TODO: Screen is being touched
	}

	LCD.WriteLine("Starting!");

	while (true)
	{
		// North-South
		// Red -> Yellow -> Green -> Walk -> Don't Walk
		red1.Write(true);
		Sleep(SLEEP);
		red1.Write(false);
		yellow1.Write(true);
		Sleep(SLEEP);
		yellow1.Write(false);
		green1.Write(true);
		Sleep(SLEEP);
		green1.Write(false);
		walk1.Write(true);
		Sleep(SLEEP);
		walk1.Write(false);
		dontWalk1.Write(true);
		Sleep(SLEEP);
		dontWalk1.Write(false);

		// East-West
		// Red -> Yellow -> Green -> Walk -> Don't Walk
		red2.Write(true);
		Sleep(SLEEP);
		red2.Write(false);
		yellow2.Write(true);
		Sleep(SLEEP);
		yellow2.Write(false);
		green2.Write(true);
		Sleep(SLEEP);
		green2.Write(false);
		walk2.Write(true);
		Sleep(SLEEP);
		walk2.Write(false);
		dontWalk2.Write(true);
		Sleep(SLEEP);
		dontWalk2.Write(false);
	}
}