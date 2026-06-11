#include "types.h"

Measure::Measure(MeasureType m, Unit u, double v)
{
	switch (m) {
	case MeasureType::FORCE:
		if (u != Unit::NEWTON)
			std::cerr << "FORCE: INVALID UNIT\n";
		else {
			mt = m;
			un = u;
			val = v;
		}
		break;
	case MeasureType::SPEED:
		if (u != Unit::MM_SEC)
			std::cerr << "SPEED: INVALID UNIT\n";
		else {
			mt = m;
			un = u;
			val = v;
		}
		break;
	case MeasureType::ENERGY:
		if (u != Unit::JOULE)
			std::cerr << "ENERGY: INVALID UNIT\n";
		else {
			mt = m;
			un = u;
			val = v;
		}
		break;
	case MeasureType::ANGLE:
		if (u != Unit::DEGREE)
			std::cerr << "ANGLE: INVALID UNIT\n";
		else {
			mt = m;
			un = u;
			val = v;
		}
		break;
	case MeasureType::PRESSURE:
		if (u != Unit::MBAR)
			std::cerr << "PRESSURE: INVALID UNIT\n";
		else {
			mt = m;
			un = u;
			val = v;
		}
		break;
	default:
		std::cerr << "MEASURETYPE NOT RECOGNIZED.\n";
	}
}
