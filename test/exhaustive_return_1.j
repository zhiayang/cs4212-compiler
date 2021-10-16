class Main
{
	Void main()
	{
		Foo f;
		Int a;
		if(true)
		{
			println(69);
		}
		else
		{
			println(420);
		}

		a = f.bar();
		println(a);
	}
}

class Foo
{
	String asdf;
	Int bar()
	{
		println("a");
		if(1 == 2)
		{
			return 69;
		}
		else
		{
			println(4);
			if(69 + 420)
			{
				asdf = "foozle";
				while(true)
				{
					println("kekw");
				}
				return 0;
			}
			else
			{
				return 1;
			}
		}
	}
}
