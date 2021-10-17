class UWU
{
	Void main()
	{
		A a;
		a = new A();

		if(a.foo() > 0 || a.bar() < 0)
		{
			println("asdf");
		}
		else
		{
			println("bsdf");
		}

		if(a.foo() == 0 && a.bar() == 0)
		{
			println("csdf");
		}
		else
		{
			println("dsdf");
		}

		while(a.uwu() == "omegalul" && (a.foo() == 1 || a.bar() == 69))
		{
			println("esdf");
		}

		while(a.uwu() == "omegalul" || (a.foo() == 1 && a.bar() == 69))
		{
			println("fsdf");
		}

		while((a.uwu() == "omegalul" || a.foo() == 1) && a.bar() == 69)
		{
			println("gsdf");
		}

		while((a.uwu() == "omegalul" && a.foo() == 1) || a.bar() == 69)
		{
			println("hsdf");
		}
	}
}

class A
{
	Int foo()
	{
		println("A::foo()");
		return 69;
	}

	Int bar()
	{
		println("A::bar()");
		return 420;
	}

	String uwu()
	{
		println("A::uwu()");
		return "kekw";
	}
}
