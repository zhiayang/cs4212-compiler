class Main
{
	Void main()
	{
		KEKW a;
		// new KEKW().foo();
		if (a.foo(69) || a.bar(420) && 1 < 2) {
			println("kekw");
		} else {
			println("asdf");
		}
		a.kek().b = ((69));
		a = new KEKW();
	}
}

class KEKW
{
	Int b;
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

	KEKW kek()
	{
		return this;
	}
}
