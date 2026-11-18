/* Hamburger navigation and Remember Last Page */
const menuButton=document.querySelector("#menu-trigger");
const menuPanel=document.querySelector("#site-menu");
const resumeLink=document.querySelector("[data-resume-link]");
const resumeLabel=document.querySelector("[data-resume-label]");
const lastPageKey="kirindl-web-preview:last-page";
const allowedPages=new Map([["#top","Home"],["#downloader","Downloader"],["pages/contact.html","Contact"],["pages/support.html","Support"],["pages/issues.html","Issues"],["pages/privacy.html","Privacy"]]);
function readLastPage(){try{const saved=JSON.parse(localStorage.getItem(lastPageKey)||"null");if(!saved||!allowedPages.has(saved.href))return null;return{href:saved.href,label:allowedPages.get(saved.href)}}catch{return null}}
function updateResume(){if(!resumeLink||!resumeLabel)return;const target=readLastPage()||{href:"#downloader",label:"Downloader"};resumeLink.href=target.href;resumeLabel.textContent=target.label}
function rememberPage(link){const href=link.getAttribute("href");if(!allowedPages.has(href))return;try{localStorage.setItem(lastPageKey,JSON.stringify({href,label:allowedPages.get(href)}))}catch{}updateResume()}
function closeMenu(){if(!menuButton||!menuPanel)return;menuPanel.hidden=true;menuButton.setAttribute("aria-expanded","false")}
function openMenu(){if(!menuButton||!menuPanel)return;menuPanel.hidden=false;menuButton.setAttribute("aria-expanded","true")}
menuButton?.addEventListener("click",()=>menuPanel.hidden?openMenu():closeMenu());
document.addEventListener("click",(event)=>{const pageLink=event.target.closest("[data-page-link]");if(pageLink)rememberPage(pageLink);if(event.target.closest(".menu-links a,[data-resume-link]"))closeMenu();if(menuPanel&&!menuPanel.hidden&&!event.target.closest(".menu-wrap"))closeMenu()});
document.addEventListener("keydown",(event)=>{if(event.key==="Escape")closeMenu()});
updateResume();
