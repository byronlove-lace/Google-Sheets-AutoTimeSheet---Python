# Auto Time Sheet GS

ATSGS asks the user what days/hours they work, calculates those times for the month and uploads that info to a time sheet on GoogleSheets

## Description

This program uses the googleapiclient library to create resources for GoogleSheets and GoogleDrive and perform the necessarry OAuth2 validations.

 The ClassTime class uses a combination of regular expressions, python's calender library and the datetime library. This Class takes user input of the weekday and hours they are working, calculates the dates and hours for that month and converts dates between strings and datetime objects to ready the info for GoogleSheets.

The DriveSearch class handles drive interactions. This is necessary because the Python GoogleSheets api can would need to make multiple api calls (1 call per cell of the GoogleSheet) in order to download and extract the GoogleSheet data in order to calculate the automated inputs. I felt this was inefficient so I decided instead to downoad the html version of the sheetfile through the GoogleDrive api (1 call). The DriveTools class I made is self-sufficient: it can take an input and download any file on GoogleDrive. It can also check for duplicates and files with the same name but different types. It will download to the downloads folder by default though it can take another path. It can also upload and has a pretty robust function for getting the media types of files (using a combination of Python's mimetypes and magic libraries).

SheetToolsPlus includes the Mapper class that I created to parse the html and map its contents to a local matrix. The MapNav class contains functions for searching and editing that matrix.

The calculated dates and times are added and the online google sheet is updated via a JSON request. 

## Progress
Currently debugging errors with the final JSON data

## Background 
I made this project to gain some experience working with webapis and json requests. I also wanted to work on a larger codebase to improve my skills with OOP.

## Challenges & Solutions
Initial challenges with this project pertained to familiarizing myself with the documentation for Google's Drive and Sheet APInitial challenges with this project pertained to familiarizing myself with the documentation for Google's Drive and Sheet API.This conisted mostly of research and micro-projects to learn the api functions used here.

The second challenge I encountered emerged when I decided to go the route of downloading and parsing the html of the google sheet. Put simply, the html tables for GoogleSheets is dynamic (the number of tds and trs representing the cells themselves change depending on whether the cell is a merged cell). In order to properly map the merge cells to the local matrix, I developed a function that reads the html table, checks the attributes of the trs and tds, and uses that to calculate the horizontal and vertial merge size while mapping the data.



