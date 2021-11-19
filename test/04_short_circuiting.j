// 04_short_circuiting.j

class Main
{
	Void main()
	{
		println(new Foo().test(10, 420));
	}
}

class Foo
{
	String test(Int x, Int y)
	{
		if(effect1() || effect2())  { println("uwu"); }
		else                        { println("??????????"); }

		while((x >= 0 && x < 7) || effect3(x)) { println("owo"); x = x - 1; }


		if(effect2() && effect3(69)) { println("oh no"); }
		else                         { println("asdf"); }

		if(!effect2() && effect3(4)) { println("oh no"); }
		else                         { println("bsdf"); }


		// all must be tried
		if(effect2() || effect2() || effect2() || effect2() || effect2() || effect1()) { println("ok"); }
		else                                                                           { println("oh no"); }

		if(effect1() && effect1() && effect1() && effect1() && effect1() && effect1()) { println("ok"); }
		else                                                                           { println("oh no"); }

		return "kekw";
	}

	Bool effect1()
	{
		println("effect 1");
		return true;
	}

	Bool effect2()
	{
		println("effect 2");
		return false;
	}

	Bool effect3(Int k)
	{
		println("effect 3");
		return k > 5;
	}
}
