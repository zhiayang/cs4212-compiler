class Main
{
	Void main()
	{
		Int a;
		Int int;
		Bool bool;
		String string;
		A o;

		o.a = o;
		o.a();
		if(true)
		{
			a = 3;
			if(1 < 2)
			{
				if(3 > 4 + 3)
				{
					a = 2 * 5 + o.b;
				}
				else
				{
					a = 0;
				}
			}
			else
			{
				return;
			}
		}
		else
		{
			while(false)
			{
				a = 2 + 3 + 3;
			}
		}

		println(a);
		println(1);
		println(-1);
		println(---------------1);
		println(true);
		println(o.getA().getB(o).b + 2 * 3 < 1 * o.b);
		println("string");

		readln(int);
		readln(bool);
		readln(string);
	}
}

class A
{
	A a;
	Int b;
	A a()
	{
		return new A();
	}

	A getA()
	{
		a = null;
		return a;
	}

	A getA(A a)
	{
		Int c;
		c = b * b;
		return a;
	}
	A getB(A a)
	{
		return null;
	}
	Void test()
	{
		return;
	}
}

class B
{
	A a;
	A getA()
	{
		return new A();
	}
}
