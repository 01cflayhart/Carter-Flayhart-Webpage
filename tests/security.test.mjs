import test from 'node:test';
import assert from 'node:assert/strict';
import { sign, verify, owner, body } from '../functions/_lib/security.js';
import { onRequest as api } from '../functions/api/[[path]].js';
import { onRequest as privatePage } from '../functions/private.js';
import { setupChecks } from '../functions/_lib/setup.js';
import configure from '../scripts/configure-cloudflare.cjs';
import cloudflareAccess from '../scripts/check-cloudflare-access.cjs';

const env = { SESSION_SECRET: 'test-only-long-secret-never-use-in-production', GITHUB_OWNER_ID: '168453384' };
const request = (path, options={}) => new Request('https://carterflayhart.pages.dev'+path, options);
test('sessions require valid HMAC, future expiry, purpose and exact owner ID', async () => {
 const good = await sign({ id: 168453384, purpose:'owner', exp:Date.now()/1000+300 },env.SESSION_SECRET);
 const req = request('/private',{headers:{Cookie:'__Host-carter_session='+good}});
 assert.ok(await owner(req,env));
 assert.equal(await verify(good+'tampered',env.SESSION_SECRET),null);
 assert.equal(await verify(good,'wrong-secret'),null);
 assert.equal(await verify(await sign({exp:1},env.SESSION_SECRET),env.SESSION_SECRET),null);
 const wrong = await sign({id:1,purpose:'owner',exp:Date.now()/1000+300},env.SESSION_SECRET);
 assert.equal(await owner(request('/private',{headers:{Cookie:'__Host-carter_session='+wrong}}),env),null);
 const oauth = await sign({id:168453384,purpose:'oauth',exp:Date.now()/1000+300},env.SESSION_SECRET);
 assert.equal(await owner(request('/private',{headers:{Cookie:'__Host-carter_session='+oauth}}),env),null);
});
test('private page contains no analytics data for anonymous visitors and cannot cache',async()=>{
  const response=await privatePage({request:request('/private'),env:{...env,GITHUB_CLIENT_ID:'test',GITHUB_CLIENT_SECRET:'test'}});
 const html=await response.text();
 assert.match(html,/Sign in with GitHub/);assert.doesNotMatch(html,/id="rows"/);
 assert.match(response.headers.get('Cache-Control'),/no-store/);
 assert.match(response.headers.get('X-Robots-Tag'),/noindex/);
 assert.equal((await api({request:request('/api/owner/stats'),env})).status,401);
});
test('unconfigured deployments explain unavailable login instead of linking to a failing endpoint',async()=>{
  const html=await(await privatePage({request:request('/private'),env})).text();
  assert.match(html,/sign-in is not available/);assert.doesNotMatch(html,/href="\/api\/auth\/start"/);
});
test('OAuth rejects preview hosts and undersized secrets before calling GitHub',async()=>{
  const auth={...env,GITHUB_CLIENT_ID:'test',GITHUB_CLIENT_SECRET:'test'};
  const preview=new Request('https://preview.carterflayhart.pages.dev/api/auth/start');
  assert.equal((await api({request:preview,env:auth})).status,403);
  assert.equal((await api({request:request('/api/auth/start'),env:{...auth,SESSION_SECRET:'short'}})).status,503);
  const response=await api({request:request('/api/auth/start'),env:auth});
  assert.equal(response.status,302);
  const target=new URL(response.headers.get('Location'));
  assert.equal(target.origin,'https://github.com');assert.equal(target.searchParams.has('scope'),false);
  assert.equal(target.searchParams.get('redirect_uri'),'https://carterflayhart.pages.dev/api/auth/callback');
});
test('owner setup checks are protected, read-only and do not expose credentials',async()=>{
  assert.equal((await api({request:request('/api/owner/setup'),env})).status,401);
  const good=await sign({id:168453384,purpose:'owner',exp:Date.now()/1000+300},env.SESSION_SECRET);
  const settings={...env,GITHUB_CLIENT_ID:'test-client',GITHUB_CLIENT_SECRET:'do-not-expose-oauth',RESEND_API_KEY:'do-not-expose-email',FEEDBACK_FROM:'sender@example.test',DB:{prepare(sql){assert.match(sql,/^SELECT/);return{async all(){return{results:[{name:'page_views'},{name:'rate_limits'}]};}};}}};
  const response=await api({request:request('/api/owner/setup',{headers:{Cookie:'__Host-carter_session='+good}}),env:settings});
  assert.equal(response.status,200);assert.equal(response.headers.get('Cache-Control'),'no-store');
  const text=await response.text();assert.doesNotMatch(text,/do-not-expose|sender@example|test-client/);
  const data=JSON.parse(text);assert.equal(data.checks.length,3);assert.ok(data.checks.every(check=>check.configured));
  assert.match(data.checks.find(check=>check.id==='email').message,/delivery has not been verified/);
  assert.equal((await setupChecks({...settings,DB:{prepare(){throw new Error('private-database-error');}}})).checks.find(check=>check.id==='database').configured,false);
  assert.ok((await setupChecks({})).checks.every(check=>!check.configured));
});
test('Cloudflare config requires a real UUID and never serializes environment secrets',()=>{
  assert.throws(()=>configure.configuration({}),/database UUID/);
  assert.throws(()=>configure.configuration({CLOUDFLARE_D1_DATABASE_ID:'REPLACE_WITH_CREATED_D1_DATABASE_ID'}),/database UUID/);
  const config=configure.configuration({CLOUDFLARE_D1_DATABASE_ID:'12345678-1234-1234-1234-123456789abc',CLOUDFLARE_API_TOKEN:'do-not-expose'});
  assert.equal(config.d1_databases[0].binding,'DB');assert.equal(config.vars.SITE_ORIGIN,'https://carterflayhart.pages.dev');
  assert.doesNotMatch(JSON.stringify(config),/do-not-expose|CLOUDFLARE_API_TOKEN/);
});
test('Cloudflare CI preflight uses only resource lookups and a read-only query',async()=>{
  const credentials={CLOUDFLARE_API_TOKEN:'synthetic-private-token',CLOUDFLARE_ACCOUNT_ID:'a'.repeat(32),CLOUDFLARE_D1_DATABASE_ID:'12345678-1234-1234-1234-123456789abc'};
  const requests=[];
  await cloudflareAccess.checkAccess(credentials,async(url,options)=>{
    requests.push({url,options});assert.equal(options.headers.Authorization,'Bearer synthetic-private-token');
    return {ok:true,status:200,async json(){return {success:true};}};
  });
  assert.equal(requests.length,2);assert.equal(requests[0].options.method,'POST');
  assert.deepEqual(JSON.parse(requests[0].options.body),{sql:'SELECT 1 AS ready'});
  assert.equal(requests[1].options.method,'GET');assert.match(requests[1].url,/\/pages\/projects\/carterflayhart$/);
  await assert.rejects(cloudflareAccess.checkAccess({...credentials,CLOUDFLARE_ACCOUNT_ID:'wrong'}),/32-character/);
  await assert.rejects(cloudflareAccess.checkAccess(credentials,async()=>({ok:false,status:403,async json(){return {success:false,errors:[{code:7403,message:'synthetic-private-token'}]};}})),error=>{
    assert.match(error.message,/7403/);assert.match(error.message,/D1 Edit/);assert.doesNotMatch(error.message,/synthetic-private-token/);return true;
  });
  await assert.rejects(cloudflareAccess.checkAccess(credentials,async()=>{throw new Error('synthetic-private-token');}),error=>{
    assert.match(error.message,/could not reach/);assert.doesNotMatch(error.message,/synthetic-private-token/);return true;
  });
});
test('missing credentials fail closed and OAuth state is mandatory',async()=>{
 assert.equal((await api({request:request('/api/auth/start'),env})).status,503);
 assert.equal((await api({request:request('/api/auth/callback?code=fake&state=fake'),env:{...env,GITHUB_CLIENT_ID:'test',GITHUB_CLIENT_SECRET:'test'}})).status,403);
});
test('cross-origin POSTs cannot send feedback, track views or change owner controls',async()=>{
 for(const path of ['/api/feedback','/api/track','/api/owner/exclude','/api/auth/logout']){
  const response=await api({request:request(path,{method:'POST',headers:{Origin:'https://evil.example','Content-Type':'application/json'},body:'{}'}),env});
  assert.equal(response.status,403);
 }
});
test('oversized request bodies are rejected and email absence is never reported as success',async()=>{
 await assert.rejects(()=>body(request('/api/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:'x'.repeat(8000)})})));
 const response=await api({request:request('/api/feedback',{method:'POST',headers:{Origin:'https://carterflayhart.pages.dev','Content-Type':'application/json'},body:'{"message":"Test only"}'}),env});
 assert.equal(response.status,503);
});
test('owner exclusion and privacy signals prevent database writes',async()=>{
 for(const headers of [{Cookie:'__Host-carter_exclude=1'},{DNT:'1'},{'Sec-GPC':'1'}]){
  const response=await api({request:request('/api/track',{method:'POST',headers:{...headers,Origin:'https://carterflayhart.pages.dev','Content-Type':'application/json'},body:'{"area":"sports"}'}),env});
  assert.equal(response.status,200);assert.equal((await response.json()).skipped,true);
 }
});
