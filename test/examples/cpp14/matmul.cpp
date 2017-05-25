#include <algorithm> // std::fill_n
#include <cstdlib> // std::atoi
#include <iostream> // std::cout, std::endl

// converts 2D coordinates into 1D coordinate
#define INDEX_2D_TO_1D(x, y, width) (((y) * (width)) + (x))

int main(int argc, char* argv[])
{
	if(argc != 4)
		return 1;

	int limit = std::atoi(argv[1]);
	int width = std::atoi(argv[2]);
	int height = std::atoi(argv[3]);

	//std::cout << limit << " times " << width << " x " << height << std::endl;

	int* a = new int[width * height]();
	int* b = new int[height * width]();
	int* c = new int[height * height]();

	std::fill_n(a, width * height, 1);
	std::fill_n(b, width * height, 1);

	for(int n = 0; n < limit; ++n)
	{
		std::fill_n(c, height * height, 0);
		for(int y = 0; y < height; ++y)
			for(int i = 0; i < width; ++i)
				for(int x = 0; x < height; ++x)
					c[INDEX_2D_TO_1D(x, y, height)] +=
							a[INDEX_2D_TO_1D(i, y, width)]
							* b[INDEX_2D_TO_1D(x, i, height)];
	}

	if(limit > 0)
		for(int y = 0; y < height; ++y)
			for(int x = 0; x < height; ++x)
				if(c[INDEX_2D_TO_1D(x, y, height)] != height)
				{
					std::cout << c[INDEX_2D_TO_1D(x, y, height)] << " - error at " << x << " x " << y << std::endl;
					return 2;
				}

	delete[] c;
	delete[] b;
	delete[] a;

	return 0;
}
