class Main
{
	Void main()
	{
		KEKW a;
		// new KEKW().foo();
		if (a.foo(69) || a.bar(420)) {
			println("kekw");
		} else {
			println("asdf");
		}
	}
}

class KEKW
{
	Bool foo(Int a)
	{
		println(a);
		return true;
	}

	Bool bar(Int a)
	{
		println(a);
		return false;
	}
}
