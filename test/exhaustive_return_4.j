class Main
{
	Void main()
	{
		A a;
		return a.foo();
	}
}

class A
{
	Int a;

	Void foo()
	{
		println(bar());
	}

	String bar()
	{
		// more complicated.
		while(true)
		{
			if(false)
			{
				return "foozle";
			}
			else
			{
				while(1 + 2 < 3)
				{
					if(69 < 420) { return "A"; } else { return "B"; }
				}
			}
		}
	}
}
