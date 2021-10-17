class Main
{
	Void main()
	{
		Foo foo;
		Int int;
		Bool bool;
		String string;

		// similar to overload_1, but tests purely on arity now
		foo = new Foo().kekw();
		int = new Foo().kekw(69);
		bool = new Foo().kekw(69, 420);
		string = new Foo().kekw(69, 420, 1337);

		println(int);
		println(bool);
		println(string);
	}
}

class Foo
{
	Foo kekw()
	{
		println("kekw()");
		return this;
	}

	Int kekw(Int a)
	{
		println("kekw(int)");
		return a + 12345;
	}

	Bool kekw(Int a, Int b)
	{
		println("kekw(int, int)");
		return a - b < 69;
	}

	String kekw(Int a, Int b, Int c)
	{
		println("kekw(int, int, int)");
		return "a + b + c";
	}
}
