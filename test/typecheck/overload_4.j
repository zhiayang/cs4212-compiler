class Main
{
	Void main()
	{
		// wrong types
		new Foo().kekw(1, "uwu");
		new Foo().kekw("uwu", "owo");
		new Foo().kekw("owo", 69420);
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
