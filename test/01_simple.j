// 01_simple.j

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

	Int bsdf(Int m)
	{
		Int k;
		Int c;
		String str;
		k = 2 * m;
		c = 500;

		str = "should have 14 chars: '";
		while(k > 0)
		{
			if(k < 8) { println("you should see this 7 times"); }
			else      { println("you should also see this 7 times"); }
			println(k);
			k = k - 1;

			str = str + "x";

			if(k == 0)
			{
				println(c + 69);
			}
			else
			{
				k = k;
			}
		}

		println(str + "'");
		println("                      -123456789abcde-");
		return k;
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

		new Foo().asdf();
		new Foo().bsdf(7);

		println("420 / 69 is:");
		println(do_divide(420, 69));
		println("69 / 420 is:");
		println(do_divide(-420, 69));
		println("420 / -69 is:");
		println(do_divide(420, -69));
		println("-420 / -69 is:");
		println(do_divide(-420, -69));

		println(do_divide(69, 420));
		println("-69 / 420 is:");
		println(do_divide(-69, 420));
		println("-420 / 69 is:");

		println("0 / 69 is:");
		println(do_divide(0, 69));

		println("69 / -69 is:");
		println(do_divide(69, -69));

		// k = 69;
		return k;
	}

	Int do_divide(Int a, Int b)
	{
		return a / b;
	}
}

