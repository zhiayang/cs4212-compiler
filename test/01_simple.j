class Main
{
	Void main()
	{
		Foo foo;
		Int k;
		Bool j;
		Bool r;

		println("asdf");
		foo.foo(69, 420, 77, 69420, 12345);

		k = 69;
		j = true;
		println(-k);
		println(420);

		r = !j;
		println(!true);
		println(!r);
	}
}

class Foo
{
	Int foo(Int x, Int y, Int z, Int w, Int m)
	{
		Int k;
		k = 3 * x + y;

		if(k == 627)
		{
			println("kekw");
			k = 2 * k;
		}
		else
		{
			println("omegalul");
			k = 5 * k;
		}

		if(w + 1 != 69420)
		{
			println("poggers");
		}
		else
		{
			println("sadge");
		}

		if(m == 12345)  { println("poggerino"); }
		else            { println("riperino"); }

		// k = 69;
		return k;
	}
}

