class Main
{
	Void main()
	{
		Int k;
		Int z;
		Bool j;
		Bool r;
		Int mm;

		println("asdf");
		z = new Foo().asdf() + new Foo().foo(69, 420, 77, 69420, 12345);

		k = 69;
		j = true;
		println(-k);
		println(420);

		r = !j;
		println(!true);
		println(!r);
		// println(z);
	}
}

class Foo
{
	Int f1;
	Int f2;
	Int f3;

	Int asdf()
	{
		return 69;
	}

	Int foo(Int x, Int y, Int z, Int w, Int m)
	{
		Int k;
		k = 3 * x + y;

		f3 = 102;
		println(k);

		m = 50;
		k = k * 1;
		if(k == 627)
		{
			println("kekw");
			k = 2 * k;
			f2 = 59 + 10;
		}
		else
		{
			println("omegalul");
			k = 5 * k;
			f2 = 19;
		}

		f1 = 420;

		if(w + 1 != 69420)
		{
			println("poggers");
		}
		else
		{
			println("sadge");
		}

		if(m == 50) { println("poggerino"); }
		else        { println("riperino"); }

		println(f1);
		println(f2);
		println(f3);

		// k = 69;
		return k;
	}
}

