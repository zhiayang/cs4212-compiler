class Main
{
	Void main()
	{
		Int k;
		Int z;
		Bool j;
		Bool r;

		println("asdf");
		z = new Foo().foo(69, 420, 77, 69420, 12345);

		k = 69;
		j = true;
		println(-k);
		println(420);

		r = !j;
		println(!true);
		println(!r);
		println(z);
	}
}

class Foo
{
	Int f1;
	Int f2;
	Int f3;

	Int foo(Int x, Int y, Int z, Int w, Int m)
	{
		Int k;
		k = 3 * x + y;
/*
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
*/
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

		println(f1);
		println(f2);
		println(f3);

		// k = 69;
		return k;
	}
}

