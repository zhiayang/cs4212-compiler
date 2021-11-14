class Main
{
	Void main()
	{
		Int int;
		Bool bool;
		String string;

		// arity
		int = new Foo().kekw(69);
		string = new Foo().kekw("omega", "lul", true);

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

	String kekw(Int a, String b)
	{
		println("kekw(int, str)");
		return "owo";
	}
}
