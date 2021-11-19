class Main
{
	Void main()
	{
		// ambiguous
		new Foo().kekw("uwu");
		new Foo().kekw("owo");
		new Foo().kekw(null);
	}
}

class Foo
{
	String kekw(String a)
	{
		println("kekw(str)");
		return "uwu";
	}

	String kekw(Foo a)
	{
		println("kekw(Foo)");
		return "owo";
	}
}
