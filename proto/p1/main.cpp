#include "types.h"

int main()
{
	Vehicle Jaguar("insertvin1", "Jaguar", "XJ",
			50, 1976, 6, 1);
	Measure f("Force", JOULE, 12);
	DoorEntry j(Jaguar, DRIVER_FRONT, f);
}
