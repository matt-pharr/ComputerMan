import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re

async def main(rcs):
    base = r'http://info.rpi.edu/directory-search/'
    async with aiohttp.ClientSession() as session:
        async with session.get(base + str(rcs)) as resp:
            # print(resp.status)
            content = await resp.text()
            soup = BeautifulSoup(content,'html.parser')
            l = []
            for a in soup.find_all('td'):
                # print(repr(str(a)))
                try:
                    # print('\n')
                    s1 = re.search('>[\s,\S]{1,}<',str(a),re.M).group(0).strip('<').strip('>').strip()
                    # print(repr(s1))
                    l.append(s1)
                except Exception as e:
                    print(e)
                    # print('\n')
                    # print("None")
                # print("\n\n")
            # for li in l:
            #     print(repr(li))
            if len(l) < 3:
                return False
            else:
                for i in range(len(l)):
                    if re.match(rcs + '@rpi.edu',l[i]) is not None:
                        # print('found')
                        return (l[i+1] == '')

async def check_is_student(rcs):
    val = await main(rcs)
    print(val)

if __name__ == "__main__":
    testcheckrcs = 'meuniv'
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_is_student(testcheckrcs))

# page = Request(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20120101 Firefox/33.0'})
# print(urlopen(page).read())