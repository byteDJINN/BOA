## OAB Files

Microsoft Outlook uses a file called the Offline Address Book (OAB) to store email information about your contacts. It is stored locally on every machine that has Outlook installed. When you type someone's name and it shows their email, this file is where that comes from. 

It just so happens that if you're connected to an AD Domain (like at school or university), it will show anybody's email, staff or student. 

## Enumerating AD Domains

But this means, theoretically, if you are connected to an AD Domain, then by reading the OAB file you could extract a list of information about every user in the same directory... names, emails, phone numbers... regardless of whether you have the privileges to do so or not. 

For 20 years, only Microsoft knew how to read the OAB file... until [antimatter15](https://github.com/antimatter15/boa) figured it out in 2014. 

Sadly, their code hasn't been updated in a long time, and it no longer works. They named the script BOA, so with some try catches, I did my best to patch BOA up. 