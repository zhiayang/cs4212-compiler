class Main
{
	Void main()
	{
		Foo foo;
		Int int;
		Bool bool;
		String string;

		// this assumes that the typechecker checks assignments correctly.
		// only if the overloads resolved correctly would the assigns succeed,
		// due to the return types of the overload set.
		int = new Foo().kekw(69, 420);
		bool = new Foo().kekw(true, false);
		string = new Foo().kekw("omega", "lul");
		foo = new Foo().kekw(new Foo(), "uwu");

		println(int);
		println(bool);
		println(string);
	}
}

class Foo
{
	Int kekw(Int a, Int b)
	{
		println("kekw(int, int)");
		return a + b;
	}

	Bool kekw(Bool a, Bool b)
	{
		println("kekw(bool)");
		return a && b;
	}

	String kekw(String a, String b)
	{
		println("kekw(str, str)");
		return a + b;
	}

	Foo kekw(Foo a, String b)
	{
		println("kekw(Foo, str)");
		return this;
	}
}
