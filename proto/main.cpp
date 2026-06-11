#include "door_entry.h"


const double STANDARD_ERROR = 10;
int main()
{
	Vehicle Jaguar("insertvin1", "Jaguar", "XJ",
			50, 1976, 6, 1);

	Measure door_force(MeasureType::FORCE, Unit::NEWTON, 220);
	Measure closing_time(MeasureType::SPEED, Unit::MM_SEC, 125); 
	Step force_over_speed(door_force, closing_time, STANDARD_ERROR);

	DoorEntry j(Jaguar, DoorType::DRIVER_FRONT, force_over_speed);
}
