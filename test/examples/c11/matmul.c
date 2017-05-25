#include <stdio.h> // printf
#include <stdlib.h> // atoi, calloc, malloc
#include <string.h> // memset

// converts 2D coordinates into 1D coordinate
#define INDEX_2D_TO_1D(x, y, width) (((y) * (width)) + (x))

int main(int argc, char* argv[])
{
	int limit;
	int width;
	int height;

	int* a;
	int* b;
	int* c;

	int n;
	int x;
	int y;
	int i;

	if(argc != 4)
		return 1;

	limit = atoi(argv[1]);
	width = atoi(argv[2]);
	height = atoi(argv[3]);

	//printf("%i times %i x %i\n", limit, width, height);

	a = (int*)malloc(width * height * sizeof(int));
	b = (int*)malloc(height * width * sizeof(int));
	c = (int*)malloc(height * height * sizeof(int));

	for(i = 0; i < width * height; ++i)
	{
		a[i] = 1;
		b[i] = 1;
	}

	for(n = 0; n < limit; ++n)
	{
		memset(c, 0, height * height * sizeof(int));
		for(y = 0; y < height; ++y)
			for(i = 0; i < width; ++i)
				for(x = 0; x < height; ++x)
					c[INDEX_2D_TO_1D(x, y, height)] +=
							a[INDEX_2D_TO_1D(i, y, width)]
							* b[INDEX_2D_TO_1D(x, i, height)];
	}

	if(limit > 0)
		for(y = 0; y < height; ++y)
			for(x = 0; x < height; ++x)
				if(c[INDEX_2D_TO_1D(x, y, height)] != height)
				{
					printf("%i - error at %i x %i\n", c[INDEX_2D_TO_1D(x, y, height)], x, y);
					return 2;
				}

	free(c);
	free(b);
	free(a);

	return 0;
}
