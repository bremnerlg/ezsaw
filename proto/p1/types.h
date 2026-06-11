#include <iostream>
#include <string>
#include <vector>

const int MAX_DAY = 31;
const int MAX_MONTH = 12;

enum class DoorType {
	DRIVER_FRONT, DRIVER_REAR, TRUNK, PASSENGER_REAR, PASSENGER_FRONT, HOOD
};

enum class TolType {
	FIXED, SAMPLED
};


enum class MeasureType {
	FORCE = 1, SPEED, ENERGY, ANGLE, PRESSURE
};

enum class Unit {
	JOULE = 6, MM_SEC, NEWTON, DEG, MBAR, DEGREE
};

struct Step {
	Measure x, y;
	double Upper, Lower;
	double Error; 
	TolType tt;

	Step(double n1, double n2, double u, double l,
	     double e, TolType t)
	: x{n1}, y{n2}, Upper{u}, Lower{l}, Error{e}, tt{t}
	{
		if (u < l)
			std::cerr << "upper cannot < lower\n";
		else {
			Upper = u;
			Lower = l;
		}
	}
	Step(double n1, double n2, double u, double l,
	     double e)
	: x{n1}, y{n2}, Upper{u}, Lower{l}, Error{e}, tt{TolType::FIXED} // fixed by default... sampled must be explicitly stated
	{
		if (u < l)
			std::cerr << "upper cannot < lower\n";
		else {
			Upper = u;
			Lower = l;
			tt = TolType::FIXED;
		}
	}

};

struct Date {
	int day, month, year;
	Date(int y, int m, int d)
	{
		if (d > MAX_DAY)
			std::cerr << "bad day.\n";
		else if (m > MAX_MONTH)
			std::cerr << "bad month.\n";
		else {
			day = d;
			month = m;
			year = y;
		}
	}
};

struct Measure {
	MeasureType mt;
	Unit un;
	double val;
	Measure(MeasureType m, Unit u, double v);
};

struct Vehicle {
	std::string VIN; /* possibly will make a VIN type to validate input */
	std::string Make;
	std::string Model;
	/* in future versions will be auto-calculated */;
	int Age;
	/* possible date type ? */

	Date ManDate;
	Vehicle(std::string v, std::string ma,
		std::string mo, int a, int y, int m,
		int d)
	: VIN(v), Make(ma), Model(mo), Age(a), ManDate(y, m, d)
	{ }
};

/* DoorEntry: Pairs test results, vehicle door for convenient manipulation and description */
struct DoorEntry {
	Vehicle v;
	DoorType t;
	Step s; 
	/* one step for testing for now, will become list */

	/* Eventually, all that will be needed to init a door entry is a VIN number, as well as the door whose results are desired. */
	DoorEntry(Vehicle ve, DoorType dt, Step es)
	: v(ve), t(dt), s(es) { }
};

