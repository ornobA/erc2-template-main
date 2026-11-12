#include <erc2.h>

// Everything in the ERC2 library is in the erc2 namespace. This line lets you
// write Motor instead of erc2::Motor, the same way `using namespace std;`
// lets you write cout instead of std::cout.
using namespace erc2;


// Declare things like motors, servos and sensors here.
// For example:
// Motor leftMotor(MotorPort0, Motor::Igwan);
// Servo arm(ServoPort0);
// DigitalEncoder leftEncoder(Pin8);


void ERCMain()
{
    // Your code here!

    // Or use the TestGUI function to test your motors, servos and sensors.
    TestGUI();
}
