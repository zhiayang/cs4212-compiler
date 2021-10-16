class Main
{
	Void main()
	{
		KEKW a;
		KEKW b;
		// new KEKW().foo();
		if (a.foo(69) || a.bar(420) && 1 < 2) {
			println("kekw");
		} else {
			println("asdf");
		}
		a.kek().b = ((69));
		a = b;
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
