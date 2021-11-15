class Main
{
	Void main()
	{
		Foo foo;
		foo.foo(69, 420);

		println("asdf");
	}
}

class Foo
{
	Int foo(Int x, Int y)
	{
		Int k;
		k = 3 * x + y;
		if(k == 1)
		{
			println("kekw");
			k = 2 * k;
		}
		else
		{
			println("omegalul");
			k = 5 * k;
		}

		return k;
	}
}
