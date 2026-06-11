#include "vehicle.h"
#include "types.h"

/* Structures dealing with the actual structure of the sql data once parsed */


struct Measure {
	MeasureType mt;
	Unit un;
	double val;
	Measure(MeasureType m, Unit u, double v);
};

struct Step {
private:
	Measure x, y;
	double Error;
	TolType tt;
public:
	Step(Measure i, Measure d, double e)
	: x{i}, y{d}, Error{e}, tt{TolType::FIXED} { } // TODO: Implement a system for sampled toltypes
};


/* DoorEntry: Pairs test results, vehicle door for convenient manipulation and description */
struct DoorEntry {
private:
	Vehicle v;
	DoorType t;
	Step s; 
	/* one step for testing for now, will become list */

	/* Eventually, all that will be needed to init a door entry is a VIN number, as well as the door whose results are desired. */
public:
	DoorEntry(Vehicle ve, DoorType dt, Step es)
	: v(ve), t(dt), s(es) { }
};

