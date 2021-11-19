// 06_fibonacci.j

class Main
{
	Void main()
	{
		Int a; Int b; Int c;

		a = 0;
		b = 1;

		while(a != 1836311903)
		{
			println(a);

			c = a + b;
			a = b;
			b = c;
		}
	}
}
