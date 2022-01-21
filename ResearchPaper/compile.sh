#!/bin/bash

pdflatex final_paper.tex
bibtex final_paper.aux
pdflatex final_paper.tex
pdflatex final_paper.tex