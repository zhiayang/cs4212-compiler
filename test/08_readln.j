// 08_readln.j

class Main
{
	Void main()
	{
		Int int;
		Bool bool;
		String string;

		readln(int);
		readln(bool);
		readln(string);

		println("your integer was:");
		println(int);

		println("your boolean was:");
		println(bool);

		println("your string was:");
		println(string);

		println("done");

		new Foo().guess(69);
	}
}

class Foo
{
	Void guess(Int num)
	{
		Int x; Int tries;

		x = 0;
		tries = 0;
		while(x != num)
		{
			readln(x);
			if(x == num) { println("uwu"); }
			else
			{
				if(x < num) { println("higher"); }
				else        { println("lower"); }
			}

			tries = tries + 1;
		}

		println("tries:");
		println(tries);
	}
}
