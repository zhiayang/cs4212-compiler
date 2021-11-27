// 02_calls.j

class Main
{
	Void main()
	{
		// maximum spillage
		println(new Foo().x());
	}
}

class Foo
{
Int x()                                                                        { return x(1); }
Int x(Int a)                                                                   { return x(a,2); }
Int x(Int a,Int b)                                                             { return x(a,b,3); }
Int x(Int a,Int b,Int c)                                                       { return x(a,b,c,4); }
Int x(Int a,Int b,Int c,Int d)                                                 { return x(a,b,c,d,5); }
Int x(Int a,Int b,Int c,Int d,Int e)                                           { return x(a,b,c,d,e,6); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f)                                     { return x(a,b,c,d,e,f,7); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g)                               { return x(a,b,c,d,e,f,g,8); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h)                         { return x(a,b,c,d,e,f,g,h,9); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i)                   { return x(a,b,c,d,e,f,g,h,i,10); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j)             { return x(a,b,c,d,e,f,g,h,i,j,11); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k)       { return x(a,b,c,d,e,f,g,h,i,j,k,12); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l)
{ return x(a,b,c,d,e,f,g,h,i,j,k,l,13); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m)
{ return x(a,b,c,d,e,f,g,h,i,j,k,l,m,14); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m,Int n)
{ return x(a,b,c,d,e,f,g,h,i,j,k,l,m,n,15); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m,Int n,Int o)
{ return x(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,16); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m,Int n,Int o,Int p)
{ return x(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,17); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m,Int n,Int o,Int p,Int q)
{ return x(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,18); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m,Int n,Int o,Int p,Int q,Int r)
{ return x(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,19); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m,Int n,Int o,Int p,Int q,Int r,
	Int s)
{ return x(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,20); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m,Int n,Int o,Int p,Int q,Int r,
	Int s,Int t)
{ return x(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,21); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m,Int n,Int o,Int p,Int q,Int r,
	Int s,Int t,Int u)
{ return x(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,22); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m,Int n,Int o,Int p,Int q,Int r,
	Int s,Int t,Int u,Int v)
{ return x(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,23); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m,Int n,Int o,Int p,Int q,Int r,
	Int s,Int t,Int u,Int v,Int w)
{ return x(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,24); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m,Int n,Int o,Int p,Int q,Int r,
	Int s,Int t,Int u,Int v,Int w,Int x)
{ return x(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,25); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m,Int n,Int o,Int p,Int q,Int r,
	Int s,Int t,Int u,Int v,Int w,Int x,Int y)
{ return x(a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,26); }
Int x(Int a,Int b,Int c,Int d,Int e,Int f,Int g,Int h,Int i,Int j,Int k,Int l,Int m,Int n,Int o,Int p,Int q,Int r,
	Int s,Int t,Int u,Int v,Int w,Int x,Int y,Int z)
{
	println(z); println(y); println(x); println(w); println(v); println(u); println(t);
	println(s); println(r); println(q); println(p); println(o); println(n); println(m);
	println(l); println(k); println(j); println(i); println(h); println(g); println(f);
	println(e); println(d); println(c); println(b); println(a);
	return 0;
}

}
