# Project Timeline (DRAFT) 📅

## September:
- Onboarding
- Host brief meeting to go over some GitHub etiquette and best practices for the project (if directors need)
- Start getting used to the discord API and discord.py library. if possible, start work on Feature #1

## October - November: -> Feature #1
- Goal: Formatting and sharing SHPE UF resources
- Create a command such as `!announcement "x"`, where x will be the contain the content of the announcement
- Will serve as a "training" of sorts, since this feature will be much easier to implement than the GBM Slide Summarization

## November - December: -> Feature #2
- Goal: GBM Slide Summarization
    - ### Tasks: 
        - Send a simple "Hello" message
        - Parse a GBM Slide, format, and print information to the console
        - Take information printed to the console, find a way to store it, and send a message
        - Develop a system to automatically parse new slides

## Mid-January - February: -> Feature #3
- Goal: Discord server moderation
    - ### Tasks:
    - Create a dummy Discord account and add it to our server
    - Create code to kick out the dummy Discord account using `discord.py`
    - **SPIKE:** Investigate a way to print the email address associated with the Discord account
        - Idea: Create a Google login where you log in to a UFL account. If successful, input the email associated with the account and add it to a DB collection. Cross-compare usernames in the set and, if not found, remove the account.

## February - Onwards: -> Extra Features
- Vote on 1-2 new tasks from the backlog and work until the end of the academic school year
