import https from 'https';

https.get('https://ai-collab-13pv.vercel.app/', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    const m = data.match(/"buildId":"([^"]+)"/);
    console.log('Build:', m ? m[1] : 'N/A');
    const chunks = [...data.matchAll(/src="(\/_next\/static\/chunks\/[^"]+\.js)"/g)];
    console.log('JS chunks:', chunks.length);
    let done = 0;
    for (const c of chunks) {
      const url = 'https://ai-collab-13pv.vercel.app' + c[1];
      https.get(url, (res2) => {
        let js = '';
        res2.on('data', chunk => js += chunk);
        res2.on('end', () => {
          if (js.includes('j6xe')) console.log(c[1].substring(c[1].lastIndexOf('/')+1), '-> NEW URL (j6xe)');
          if (js.includes('49ld')) console.log(c[1].substring(c[1].lastIndexOf('/')+1), '-> OLD URL (49ld)');
          const wsMatch = js.match(/wss?:\/\/[^"'\\s)]+/);
          if (wsMatch) console.log(c[1].substring(c[1].lastIndexOf('/')+1), 'WS:', wsMatch[0]);
          done++;
          if (done === chunks.length) console.log('Done');
        });
      });
    }
  });
}).on('error', e => console.log('Error:', e.message));
