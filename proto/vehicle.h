#include <string>
#include <iostream>

/* Supporting data structures for vehicle entries */

struct Date {
private:
	int day, month, year;
	static const int MAX_DAY = 31;
	static const int MAX_MONTH = 12;

public:
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


struct Vehicle {
private:
	std::string VIN; /* possibly will make a VIN type to validate input */
	std::string Make;
	std::string Model;
	/* in future versions will be auto-calculated */;
	int Age;
	/* possible date type ? */
public:
	Date ManDate;
	Vehicle(std::string v, std::string ma,
		std::string mo, int a, int y, int m,
		int d)
	: VIN(v), Make(ma), Model(mo), Age(a), ManDate(y, m, d)
	{ }
};

