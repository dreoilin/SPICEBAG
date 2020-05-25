%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Tiarnach Ó Riada's Engineering report class
%% 
%% Sample usage shown below
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%\documentclass[article,twocolumn]{TOREngReport}
%
%\begin{document}
%% Define report details
%\TOREngReportDetails{Lab 4|Minor Project Part 1}{EEEN30110 Signals \& Systems}{UCD}{Tiarnach \'O Riada 16315466}
%\maketitle
%
%\pagenumbering{roman}
%\pagestyle{preface}
%\tableofcontents
%\cleardoublepage
%
%\pagenumbering{arabic}
%\pagestyle{body}
%% FOR EACH SECTION
%\include{src/p1}


%% APPENDICES
%\begin{appendix}
%\end{appendix}
%\end{document}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\ProvidesClass{TOREngReport}[2019/11/06 Class for engineering reports]
\NeedsTeXFormat{LaTeX2e}
\def\baseclass{article}
%% Article options
\DeclareOption{article}{
	\DeclareOption{10pt}{\PassOptionsToClass{\CurrentOption}{article}}
	\DeclareOption{twocolumn}{\PassOptionsToClass{\CurrentOption}{article}}
}
\DeclareOption{report}{
	\DeclareOption{10pt}{\PassOptionsToClass{\CurrentOption}{report}}
	\DeclareOption{twocolumn}{\PassOptionsToClass{\CurrentOption}{report}}
	\def\baseclass{report}
}
%\DeclareOption{12pt}{\PassOptionsToClass{\CurrentOption}{article}}
\DeclareOption{problem}{\def\isproblemsheet{1}}
\DeclareOption{question}{\def\isquestionsheet{1}}
\DeclareOption{minted}{\def\@mint{1}}
\DeclareOption{breqn}{\def\@breqninc{1}}
\DeclareOption{matlab}{
	\def\ismatlab{1}
}
\DeclareOption{endfloat}{\def\endfloat}
\DeclareOption*{
	\ClassWarning{TOREngReport}{Unknown option '\CurrentOption'}
}

%\ExecuteOptions{10pt}
\ProcessOptions*
\LoadClass{\baseclass}
%\renewcommand{\normalsize}{\fontsize{9}{10}\selectfont}
\setlength{\textwidth}{280mm}
\setlength{\textheight}{193mm}

\RequirePackage[utf8]{inputenc}
\RequirePackage[a4paper,margin=2cm]{geometry}
\RequirePackage{fancyhdr}
\RequirePackage[en-IE]{datetime2}
%\DTMsetdatestyle{ddmmyyyy}
%\RequirePackage{lastpage}
%\RequirePackage[french]{babel}
%\RequirePackage{setspace, booktabs, url}
\RequirePackage{subcaption}
\RequirePackage{dblfloatfix}
\RequirePackage[pdftex]{graphicx}
\RequirePackage[numbers]{natbib}
%\RequirePackage{wrapfig}
%\RequirePackage[T1]{fontenc}
\RequirePackage[font=small, labelfont=bf]{caption}
\RequirePackage{helvet}

\RequirePackage{cuted} % provides strip environment for 1 col in 2 col doc

\RequirePackage{siunitx}
\RequirePackage{amsmath}
\RequirePackage{amssymb}
\RequirePackage{mathtools}
\RequirePackage{mathrsfs}
\RequirePackage[table]{xcolor}
\RequirePackage{tikz}
\RequirePackage{tikz-3dplot}
\RequirePackage{circuitikz}
\RequirePackage{standalone}
%\RequirePackage[protrusion=true, expansion=true]{microtype}
%\RequirePackage{sectsty}
%\RequirePackage{flafter}
%\RequirePackage{algorithm}
\RequirePackage{booktabs}
%\RequirePackage{listings,xcolor, amssymb}
\ifx\undefined\@breqninc

\else
\RequirePackage{breqn}
\fi
\ifx\undefined\@mint

\else
	\RequirePackage{minted}
	\RequirePackage{xcolor}
	\RequirePackage{calc}
	\usemintedstyle{tango}
	\definecolor{lbcolor}{rgb}{0.95,0.95,0.95}
	\setminted{
		escapeinside=||,
		fontfamily=courier,
		fontseries=bf,
		frame=leftline,
		framerule=1pt,
		framesep=6pt,
		rulecolor=black,
		numbers=left,
		numbersep=3pt,
		numberblanklines=true,
		samepage=true,
		%bgcolor=lbcolor,
		breaklines=true,
		breaksymbol={\color{red}$\hookrightarrow$},
		tabsize=2,
		%xleftmargin=-5cm
	}
	\ifx\ismatlab\undefined

	\else
		\RequirePackage{xcolor}
		\RequirePackage{calc}
		\RequirePackage{matlab-prettifier}
		\definecolor{com-green}{rgb}{034,139,034}
		\lstdefinestyle{matlab}{
			style=Matlab-editor,
			title=\lstname,
			escapeinside={|}{|},
%			autogobble,
			basicstyle=\footnotesize\ttfamily,
%			fontfamily=courier,
%			fontseries=bf,
			frame={left bottom},
			framerule=1pt,
			framesep=2pt,
			numbers=left,
			numbersep=4pt,
			numberstyle=\tiny\bfseries\color{black},
			numberblanklines=true,
			rulecolor=\color{black},
%			samepage=true,
%			bgcolor=lbcolor,
			breaklines=true
%			breaksymbol={\color{red}$\hookrightarrow$}
		}
		\definecolor{lbcolor}{rgb}{0.95,0.95,0.95}
		\setminted[matlab]{
			autogobble,
			escapeinside=||,
			fontfamily=\ttfamily,
			fontseries=bf,
			frame=leftline,
			framerule=1pt,
			framesep=2pt,
			rulecolor=black,
			numbers=left,
%			numberstyle=\tiny\bfseries\color{black},
			numbersep=4pt,
			numberblanklines=true,
			samepage=true,
%			bgcolor=lbcolor,
			breaklines=true,
			breaksymbol={\color{red}$\hookrightarrow$}
		}
	\fi
\fi

\RequirePackage{listings}
\lstset{basicstyle=\ttfamily,frame=l}

\ifx\ismatlab\undefined

\else
	\lstset{language=matlab}
	\def\matlab{{\textsc{Matlab} }}
\fi

%\RequirePackage{algorithmicx}
\RequirePackage[toc,page]{appendix}
\RequirePackage{titlesec}

\RequirePackage[hidelinks,pdftex,backref,
%pdfauthor=\@authors,
%pdftitle=\@title,
%pdfsubject=\@subject,
%pdfkeywords=\@keywords,
pdfproducer={Latex with hyperref},
pdfcreator={pdflatex}]{hyperref}

\RequirePackage{cleveref}
%\graphicspath{ {./images/} }
\RequirePackage{suffix}

\DeclareCaptionType{captioneq}[][List of equations]
\renewcommand{\captioneqname}{Equation}
\DeclareCaptionLabelFormat{captioneqfmt}{#1 \theequation}
\captionsetup[captioneq]{labelformat=captioneqfmt}


\newcommand{\HRule}[1]{\rule{\linewidth}{#1}}
%\onehalfspacing
\setcounter{tocdepth}{5}
\setcounter{secnumdepth}{5}

% Reference formatting
\def\sectionautorefname{\S}
\def\subsectionautorefname{\S}
\def\subsubsectionautorefname{\S}
\def\algorithmautorefname{Algorithm}
\renewcommand{\ref}[1]{\cref{#1}}

% Counter formatting
\renewcommand\theenumi{\roman{enumi}}
\renewcommand\theenumii{\alph{enumii}}
\renewcommand\theenumiii{\roman{enumiii}}

% MATHS BITS
\DeclarePairedDelimiter\abs{\lvert}{\rvert}%
\DeclarePairedDelimiter\norm{\lVert}{\rVert}%

% Frames
\DeclareRobustCommand*{\ora}{\overrightarrow}
\newcommand{\Frame}[1]{$\ora{E}$\textsuperscript{#1}}
\newcommand{\mFrame}[1]{\ora{E}^{#1}}
\newcommand{\axis}[2]{\Frame{#1}\textsubscript{#2}}
\newcommand{\maxis}[2]{\mFrame{#1}_{#2}}

% Vectors
\renewcommand{\vec}[1]{\textbf{\textit{#1}}}
\newcommand{\tvec}[1]{$\ora{#1}$}
\newcommand{\mvec}[1]{\ora#1}
\newcommand{\colvec}[1]{\underline{#1}}

% Matrices
\newcommand{\mat}[1]{\textbf{$\mathcal{#1}$}}
\newcommand{\sqmat}[1]{\underline{\underline{#1}}}

% turmeric
\newcommand{\turmeric}{\textit{Turmeric} }

% Transformy bois
\def\fourier{\mathscr{F}}
\def\laplace{\mathscr{L}}
\newcommand\series[2]{\mathcal{S}_n\left(#1{\scriptstyle \left(#2\right)}\right)}
\newcommand\transform[1]{\mathcal{#1}}

% Exponential
\renewcommand{\exp}[1]{e^{#1}}

% Fancy equals
\newcommand{\equalexpl}[1]{%
	\underset{\substack{\uparrow\\\mathrlap{\text{\hspace{-1em}#1}}}}{=}}

\newcommand{\mLabel}[1]{\mbox{$\textstyle{#1}$}}

% Circled letters
\newcommand{\lcirc}[1]{\large\textcircled{\footnotesize \textbf{$#1$}}}
%-------------------------------------------------------------------------------
% HEADER & FOOTER
%-------------------------------------------------------------------------------
\pagestyle{fancy}
\fancyhf{}

\fancypagestyle{body}{
	\setlength\headheight{15pt}
	\fancyhead[L]{\thesubject}
	\fancyhead[R]{\theinstitution}
	\fancyfoot[L]{\theauthors}
	\fancyfoot[R]{\thepage}

	\renewcommand{\headrulewidth}{1pt}
	\renewcommand{\footrulewidth}{1pt}
}
\fancypagestyle{preface}{
	\setlength\headheight{15pt}
	\fancyhead[L]{\thesubject}
	\fancyhead[R]{\theinstitution}
	\fancyfoot[L]{\theauthors}
	\fancyfoot[R]{\thepage}

	\renewcommand{\headrulewidth}{1pt}
	\renewcommand{\footrulewidth}{1pt}
}

%% TABLE OF CONTENTS
%\renewcommand{\cfttoctitlefont}{\hfill\Huge}

%% --------------------------------
\def\thetitle{ }
\def\thesubject{ }
\def\theinstitution{ }
\def\theauthors{ }
\newcommand{\TOREngReportDetails}[4]{
	\def\thetitle{#1}
	\def\thesubject{#2}
	\def\theinstitution{#3}
	\def\theauthors{#4}
}

\newcommand{\AbstractBox}[1]{
	\def\theabstract{#1}
}

%
% TITLE PAGE
%
\RequirePackage{anyfontsize}
\RequirePackage{setspace}

\renewcommand{\maketitle}{
	\pagenumbering{gobble}
	\begin{titlepage}
		\thispagestyle{empty}
		\begin{minipage}{\linewidth}
			\parbox{0.2\linewidth}{\includegraphics[width=0.5\linewidth]{ucd-crest.png}\hfill}%
			\parbox{0.2\linewidth}{\theinstitution\hfill{\fontsize{38}{10}$/$}}%
			\parbox{0.3\linewidth}{\parbox{0.8\linewidth}{\raggedright School of Engineering and Architecture}\hfill{\fontsize{40}{10} $/$}}%
			\parbox{0.3\linewidth}{\parbox{0.8\linewidth}{\raggedright Electrical and Electronic Engineering}\hfill{\fontsize{40}{10} $/$}}%
		\end{minipage}
		
		\vspace{3cm}
		\begingroup
		\setstretch{4}\fontsize{38}{10}\selectfont\fontdimen2\font=0.8ex
		\parbox{0.7\textwidth}{\raggedright\textbf{\thetitle}}
		\endgroup
		
		\ifx\theabstract\undefined
			\vspace{\fill}
		\else
			\vspace{\fill}%
			\hspace{0.1\textwidth}\parbox{0.8\textwidth}{\theabstract}%
			\vspace{\fill}%
		\fi

		\parbox{\linewidth}{{\large 
				{\Large\textbf{\thesubject}}
				
				\bigskip
				\textbf{Authors} : \theauthors
				
				\smallskip
				\textbf{Date submitted} : \DTMtoday
		}}
	\end{titlepage}
	\clearpage
}

\crefname{lstlisting}{listing}{listings}
\Crefname{lstlisting}{Listing}{Listings}
%%
% Custom sections

% QUESTION
\ifx\isquestionsheet\undefined

\else

\newcounter{question}[section]
\crefname{question}{question}{questions}
\Crefname{question}{Question}{Questions}
\newcounter{subquestion}[question]
\crefname{subquestion}{question}{questions}
\Crefname{subquestion}{Question}{Questions}
%\crefformat{subquestion}{question~#2#1#3}
\newcounter{subsubquestion}[subquestion]
\crefname{subsubquestion}{question}{questions}
\Crefname{subsubquestion}{Question}{Questions}

\newcommand{\question}{%
	
	
	\refstepcounter{question}{\normalfont\Large\bfseries Question \thequestion}
	\label{q:\thequestion}
	\setcounter{figure}{0}
	\addcontentsline{toc}{section}{Question \thequestion}
	\\\smallskip}

\newcommand\subquestion[1][]{%
	\vspace{\baselineskip}
	\def\subquestiontext{\thequestion$\vert$\thesubquestion\ifblank{#1}{}{ #1}}%
	\refstepcounter{subquestion}%
	{\normalfont\normalsize\bfseries \subquestiontext}%
	\label{q:\thequestion:\thesubquestion}%
	\addcontentsline{toc}{subsection}{\thequestion.\thesubquestion}%
	\\\smallskip}

\WithSuffix\newcommand\subquestion*[1]{
	\def\subquestiontext{#1}%
	{\normalfont\normalsize\bfseries \thequestion\hspace{2pt}\subquestiontext}%
	\hypertarget{sq:\subquestiontext}{}%
	\label{sq:\subquestiontext}
	\addcontentsline{toc}{subsection}{\thequestion\hspace{2pt}\subquestiontext}%
	\\}

	\renewcommand\contentsname{Questions}
	\renewcommand{\thefigure}{\arabic{question}.\arabic{figure}}
\fi

%PROBLEM
\ifx\isproblemsheet\undefined

\else

	\newcounter{problem}[section]
	\crefname{problem}{problem}{problems}
	\Crefname{problem}{Problem}{Problems}
	\newcommand\problem{
		
		
		\bigskip
		\refstepcounter{problem}{\normalfont\Large\bfseries Problem \theproblem}
		\label{p:\theproblem}
		\setcounter{figure}{0}
		\addcontentsline{toc}{section}{Problem \theproblem}
		\\\smallskip}
	\newcounter{subproblem}[problem]
	\crefname{subproblem}{problem}{problems}
	\Crefname{subproblem}{Problem}{Problems}
	\newcommand\subproblem{\refstepcounter{subproblem}{\normalfont\normalsize\bfseries \arabic{problem}$\vert$\arabic{subproblem}}
		\label{p:\theproblem:\thesubproblem}
		\addcontentsline{toc}{subsection}{\thesubproblem}
		\\\smallskip}
	
	\renewcommand\contentsname{Problems}
	\renewcommand{\thefigure}{\arabic{problem}.\arabic{figure}}
\fi

%%%%%%%%%%%%
%% FLOATS %%
%%%%%%%%%%%%
\ifx\undefined\endfloat

\else
\usepackage[nomarkers,figuresonly]{endfloat}
\renewcommand{\listoffigures}{}
\fi

% FFIGURES  Insert figures for filenames given
%	#1 List of filenames, captions and labels in the format fn/cap/lab
\newcommand{\ffigures}[1]{%
	\foreach \fn / \capn / \lab in {#1}{%
		\begin{figure*}
			\centering
			\includegraphics[width=\linewidth]{\fn}
			\caption{\capn}
			\label{\lab}
		\end{figure*}
		
}}

%% SUBFIGMAT  Insert matrix of figures
%	#1 2D array of subfigures in the format 
%			{lenf/{f1/c1/l1 , f2/c2/l2,...},leng/{g1/cg1/lg1,...},...}
\newcommand{\subfigmat}[2]{%
	\begin{figure*}
		\centering
		\foreach \len / \line in {#1}{%
			\FPeval{\subfigwidthfrac}{round(1/\len,6)}%
			\foreach \fig / \capn / \lab in \line{%
				\begin{subfigure}{\subfigwidthfrac\linewidth}
					\centering
					\includegraphics[width=\linewidth]{\fig}
					\caption{\capn}
					\label{fig:\lab}
				\end{subfigure}\hfill%
			}%
			\newline%
		}%
		\foreach \capn / \lab in {#2}{%
			\caption{\capn}%
			\label{fig:\lab}%
		}
	\end{figure*}
}

%%%%%%%%%%%%
%% IMAGES %%
%%%%%%%%%%%%
\graphicspath{ {./img/} }
