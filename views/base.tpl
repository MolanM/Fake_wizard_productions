<!DOCTYPE html>
<html lang="en">
<head>
<title>Ponarejevalci denarja</title>
<meta charset="utf-8">
<link rel="stylesheet" href="/static/css/reset.css" type="text/css" media="all">
<link rel="stylesheet" href="/static/css/layout.css" type="text/css" media="all">
<link rel="stylesheet" href="/static/css/style.css" type="text/css" media="all">
</head>
%if stran:
<body id={{stran}}>
%else:
<body id="page1">
%end
<div class="bg1">
  <div class="main">
    <!--header -->
    <header>
      <nav>
        <ul id="menu">
          <li 
		  %if aktivna == "Skupina":
		  class="active"
		  %end
		  ><a href="/index/">Skupina</a></li>
          <li
		  %if aktivna == "Dogodki":
		  class="active"
		  %end
		  ><a href="/dogodki/">Dogodki</a></li>
          <li
		  %if aktivna == "Galerija":
		  class="active"
		  %end
		  ><a href="/galerija/">Galerija</a></li>
          <li
		  %if aktivna == "Člani":
		  class="active"
		  %end
		  ><a href="/clani/">Člani</a></li>
          <li
		  %if aktivna == "Oboževalci":
		  class="active"
		  %end
		  ><a href="/uporabniki/">Oboževalci</a></li>
          <li
		  %if aktivna == "Kontakt":
		  class="active"
		  %end
		  ><a href="/kontakt/">Kontakt</a></li>
        </ul>
      </nav>
      <h1><a href="/index/" id="logo">Ponarejevalci denarja feel the rhythm</a></h1>
	  <div id="uporabnik">
		%if prijavljen_uporabnik is not None:
		<h3><a href="/user/{{id_uporabnik}}/" style="text-decoration: none">{{prijavljen_uporabnik}}</a></h3>
		<center class="color2">Stanje: {{stanje}}</center>
		<a href="/logout/">Odjava</a>
		%else:
		<br>
		<center><a href="/prijava/">Prijava</a> ali
		<a href="/register/">Registracija</a></center>
		%end
	  </div>
    </header>
    <!--header end-->
    <div class="box">
      <!--content -->
      <article id="content">
      {{!base}}
      </article>
      <!--content end-->
      <!--footer -->
      <footer>
        <div class="line1">
          <div class="line2 wrapper">
            <div class="icons">
              <h4>Povezave</h4>
              <ul id="icons">
                <li><a href="https://twitter.com/rtv_slovenija/status/280742214936698880" class="normaltip"><img src="/static/images/icon3.jpg" alt=""></a></li>
                <li><a href="https://www.facebook.com/ponarejevalci/" class="normaltip"><img src="/static/images/icon4.jpg" alt=""></a></li>
              </ul>
              <!-- {%FOOTER_LINK} -->
            </div>
            <div class="info">
              <h4>Naše delo</h4>
              <ul>
				<li><a href="/dogodki/">Dogodki</a></li>
				<li><a href="/pesmi/">Pesmi</a></li>
				<li><a href="/albumi/">Albumi</a></li>
                <li><a href="/litdela/">Lit. dela</a></li>
              </ul>
            </div>
            <div class="info">
              <h4>Oboževalci</h4>
              <ul>
                <li><a href="/prijava/">Prijava</a></li>
				<li><a href="/register/">Registracija</a></li>
				<li><a href="/uporabniki/">Vsi oboževalci</a></li>
                <li><a href="/logout/">Odjava</a></li>
              </ul>
            </div>
            <div class="phone">
              <h4>Vstopnice</h4>
              <p>Telefon<span>01-476-6500-NIGHT</span></p>
            </div>
          </div>
      </footer>
      <!--footer end-->
    </div>
  </div>
</div>
</body>
</html>