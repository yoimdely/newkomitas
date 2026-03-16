// ============================================================
//  CORE LIBRARIES (GLOBAL INJECTION FROM CDN)
// ============================================================
// gsap, ScrollTrigger, and Lenis are now provided globally via index.html scripts

gsap.registerPlugin(ScrollTrigger)

// ============================================================
//  SMOOTH SCROLL (LENIS)
// ============================================================
const lenis = new Lenis({
    lerp: 0.07,
    smoothWheel: true,
    syncTouch: false,
    gestureOrientation: 'vertical',
    touchMultiplier: 1.5,
    infinite: false,
})

lenis.on('scroll', ScrollTrigger.update)

gsap.ticker.add((time) => {
    lenis.raf(time * 1000)
})
gsap.ticker.lagSmoothing(0)

// ============================================================
//  PRELOADER — dismiss on load or after 2s timeout (whichever first)
// ============================================================
let heroDone = false

function dismissPreloader() {
    if (heroDone) return
    heroDone = true
    const preloader = document.getElementById('preloader')
    if (preloader) {
        setTimeout(() => {
            preloader.classList.add('loaded')
            setTimeout(runHeroIntro, 300)
        }, 1400)
    } else {
        runHeroIntro()
    }
}

// Fires when images/fonts all loaded
window.addEventListener('load', dismissPreloader)
// Fallback: fire after 2.5s no matter what (handles file:// protocol edge cases)
setTimeout(dismissPreloader, 2500)
// Even earlier fallback
document.addEventListener('DOMContentLoaded', () => setTimeout(dismissPreloader, 2000))

// ============================================================
//  HERO CINEMATIC INTRO
// ============================================================
function runHeroIntro() {
    const tl = gsap.timeline({ defaults: { ease: 'power4.out' } })

    // Nav
    tl.fromTo('.premium-nav',
        { opacity: 0, y: -20 },
        { opacity: 1, y: 0, duration: 1 },
        0
    )

    // Ambient background reveal
    tl.fromTo('#heroBg',
        { scale: 1.08, opacity: 0.72, filter: 'brightness(0.75)' },
        { scale: 1, opacity: 1, filter: 'brightness(1)', duration: 2.2, ease: 'power3.inOut' },
        0
    )
    tl.fromTo(['.hero-ambient-orb', '.hero-ambient-diagonal', '.hero-ambient-frame'],
        { opacity: 0, scale: 0.92 },
        { opacity: 1, scale: 1, duration: 1.6, stagger: 0.08, ease: 'power3.out' },
        0.2
    )

    // Architectural lines
    tl.fromTo('.hero-line.left',
        { scaleY: 0, transformOrigin: 'top' },
        { scaleY: 1, duration: 1.8, ease: 'power3.out' },
        0.3
    )
    tl.fromTo('.hero-line.right',
        { scaleY: 0, transformOrigin: 'bottom' },
        { scaleY: 1, duration: 1.8, ease: 'power3.out' },
        0.5
    )
    tl.fromTo('.hero-line.bottom',
        { scaleX: 0, transformOrigin: 'left' },
        { scaleX: 1, duration: 1.2, ease: 'power3.out' },
        0.8
    )

    // Text reveals (staggered)
    tl.fromTo('.reveal-text',
        { y: 60, skewY: 4, opacity: 0 },
        { y: 0, skewY: 0, opacity: 1, duration: 1.4, stagger: 0.12, ease: 'power3.out' },
        0.8
    )

    // Form and scroll indicators
    tl.fromTo(['#heroForm', '#scrollIndicator', '.hero-corner-tag'],
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 1, stagger: 0.15 },
        1.4
    )
}

// ============================================================
//  NAV — SCROLL STATE
// ============================================================
const nav = document.getElementById('nav')
if (nav) {
    ScrollTrigger.create({
        start: 'top -60',
        onUpdate: (self) => {
            if (self.scroller.scrollTop > 60 || self.progress > 0) {
                nav.classList.add('scrolled')
            } else {
                nav.classList.remove('scrolled')
            }
        }
    })

    // Simpler approach using scroll listener via lenis
    lenis.on('scroll', ({ scroll }) => {
        if (scroll > 60) {
            nav.classList.add('scrolled')
        } else {
            nav.classList.remove('scrolled')
        }
    })
}

// ============================================================
//  FADE-UP ELEMENTS (IntersectionObserver — no GSAP overhead)
// ============================================================
const fadeObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible')
            fadeObserver.unobserve(entry.target)
        }
    })
}, { threshold: 0.12, rootMargin: '0px 0px -50px 0px' })

document.querySelectorAll('.fade-up').forEach(el => fadeObserver.observe(el))

// ============================================================
//  IMAGE REVEAL MASKS (GSAP clip-path)
// ============================================================
document.querySelectorAll('.reveal-mask').forEach(wrap => {
    gsap.fromTo(wrap,
        { clipPath: 'inset(100% 0 0 0)' },
        {
            clipPath: 'inset(0% 0 0 0)',
            duration: 1.6,
            ease: 'expo.inOut',
            scrollTrigger: {
                trigger: wrap,
                start: 'top 82%',
            }
        }
    )

    // Parallax on inner image
    const img = wrap.querySelector('img')
    const speed = parseFloat(wrap.dataset.speed) || 1
    if (img && speed !== 1) {
        gsap.to(img, {
            yPercent: (speed - 1) * 100 * 0.4,
            ease: 'none',
            scrollTrigger: {
                trigger: wrap,
                start: 'top bottom',
                end: 'bottom top',
                scrub: true
            }
        })
    }
})

// ============================================================
//  HERO IMAGE PARALLAX
// ============================================================
gsap.to('#heroBg', {
    yPercent: 15,
    ease: 'none',
    scrollTrigger: {
        trigger: '.hero-section',
        start: 'top top',
        end: 'bottom top',
        scrub: true
    }
})

// ============================================================
//  CTA BACKGROUND PARALLAX
// ============================================================
gsap.to('#ctaBg', {
    yPercent: 12,
    ease: 'none',
    scrollTrigger: {
        trigger: '.cta-section',
        start: 'top bottom',
        end: 'bottom top',
        scrub: true
    }
})

// ============================================================
//  ANIMATED COUNTERS
// ============================================================
const counters = document.querySelectorAll('.counter')
let countersAnimated = false

ScrollTrigger.create({
    trigger: '#counters',
    start: 'top 80%',
    onEnter: () => {
        if (countersAnimated) return
        countersAnimated = true

        counters.forEach(counter => {
            const target = +counter.getAttribute('data-target')
            gsap.to(counter, {
                innerHTML: target,
                duration: target > 100 ? 2.5 : 1.8,
                snap: { innerHTML: 1 },
                ease: 'power2.out'
            })
        })
    }
})

// ============================================================
//  GALLERY — SHOW MORE + LIGHTBOX
// ============================================================
const loadMoreBtn = document.getElementById('loadMoreGallery')
const hiddenItems = document.querySelectorAll('.hidden-gallery')
const videoPresentationTrigger = document.getElementById('videoPresentationTrigger')
const plansGrid = document.getElementById('plansGrid')
const togglePlansCatalog = document.getElementById('togglePlansCatalog')
const extraPlanCards = plansGrid ? plansGrid.querySelectorAll('.plan-card--extra') : []
const managerModal = document.getElementById('managerModal')
const managerModalClosers = managerModal?.querySelectorAll('[data-manager-close]') || []
const managerModalOpeners = document.querySelectorAll('[data-manager-open]')

if (loadMoreBtn && hiddenItems.length > 0) {
    loadMoreBtn.addEventListener('click', () => {
        hiddenItems.forEach((item, i) => {
            item.style.display = 'block'
            gsap.fromTo(item,
                { opacity: 0, y: 30 },
                { opacity: 1, y: 0, duration: 0.7, delay: i * 0.08, ease: 'power2.out' }
            )
        })
        loadMoreBtn.closest('.text-center').style.display = 'none'
        ScrollTrigger.refresh()
    })
}

if (togglePlansCatalog && plansGrid && extraPlanCards.length > 0) {
    togglePlansCatalog.addEventListener('click', () => {
        const isExpanded = plansGrid.classList.toggle('is-expanded')
        const nextLabel = isExpanded ? togglePlansCatalog.dataset.expandedLabel : togglePlansCatalog.dataset.collapsedLabel
        if (nextLabel) togglePlansCatalog.textContent = nextLabel

        if (isExpanded) {
            extraPlanCards.forEach((card, index) => {
                gsap.fromTo(card,
                    { opacity: 0, y: 28 },
                    { opacity: 1, y: 0, duration: 0.55, delay: index * 0.07, ease: 'power2.out' }
                )
            })
        } else {
            lenis.scrollTo('#plans', { offset: -80, duration: 1 })
        }

        ScrollTrigger.refresh()
    })
}

function openManagerModal() {
    if (!managerModal) return
    managerModal.classList.add('active')
    managerModal.setAttribute('aria-hidden', 'false')
    document.body.classList.add('modal-open')
    lenis.stop()
}

function closeManagerModal() {
    if (!managerModal) return
    managerModal.classList.remove('active')
    managerModal.setAttribute('aria-hidden', 'true')
    document.body.classList.remove('modal-open')
    lenis.start()
}

window.closeManagerModal = closeManagerModal

managerModalOpeners.forEach((button) => {
    button.addEventListener('click', (event) => {
        event.preventDefault()
        openManagerModal()
    })
})

managerModalClosers.forEach((button) => {
    button.addEventListener('click', closeManagerModal)
})

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && managerModal?.classList.contains('active')) {
        closeManagerModal()
    }
})

// Lightbox
const lightbox = document.getElementById('lightbox')
const lightboxImg = document.getElementById('lightbox-img')
const lightboxVideo = document.getElementById('lightboxVideo')
const lightboxClose = document.getElementById('lightboxClose')
const lightboxPrev = document.getElementById('lightboxPrev')
const lightboxNext = document.getElementById('lightboxNext')

let lightboxImages = []
let currentLightboxIndex = 0
let currentLightboxGroup = ''

function resolveLightboxSource(item) {
    const image = item.querySelector('img')
    if (image?.currentSrc) return image.currentSrc
    if (image?.src) return image.src

    const rawSrc = item.getAttribute('data-src')
    if (!rawSrc) return ''

    try {
        return new URL(rawSrc, window.location.href).href
    } catch (error) {
        return rawSrc
    }
}

function buildLightboxImages(groupName) {
    currentLightboxGroup = groupName
    lightboxImages = []
    document.querySelectorAll(`.lightbox-trigger[data-lightbox-group="${groupName}"]`).forEach((item) => {
        const src = resolveLightboxSource(item)
        const alt = item.querySelector('img')?.alt || ''
        if (src) lightboxImages.push({ src, alt })
    })
}

function openLightboxImage(groupName, index) {
    if (!lightbox || !lightboxImg) return
    buildLightboxImages(groupName)
    if (!lightboxImages.length || !lightboxImages[index]) return
    currentLightboxIndex = index
    lightbox.classList.remove('is-video')
    lightboxImg.src = lightboxImages[index].src
    lightboxImg.alt = lightboxImages[index].alt
    if (lightboxVideo) lightboxVideo.src = ''
    lightbox.classList.add('active')
    lenis.stop()
    document.body.style.overflow = 'hidden'
}

function openLightboxVideo(videoId) {
    if (!lightbox || !lightboxVideo) return
    lightbox.classList.add('active', 'is-video')
    lightboxVideo.src = `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0&modestbranding=1`
    if (lightboxImg) {
        lightboxImg.src = ''
        lightboxImg.alt = ''
    }
    lenis.stop()
    document.body.style.overflow = 'hidden'
}

function closeLightbox() {
    if (!lightbox) return
    lightbox.classList.remove('active')
    lenis.start()
    document.body.style.overflow = ''
    setTimeout(() => {
        lightbox.classList.remove('is-video')
        if (lightboxImg) lightboxImg.src = ''
        if (lightboxVideo) lightboxVideo.src = ''
    }, 400)
}

function showLightboxImage(index) {
    if (!lightboxImages.length || lightbox.classList.contains('is-video')) return
    currentLightboxIndex = (index + lightboxImages.length) % lightboxImages.length
    if (lightboxImg) {
        gsap.to(lightboxImg, {
            opacity: 0, scale: 0.95, duration: 0.2,
            onComplete: () => {
                lightboxImg.src = lightboxImages[currentLightboxIndex].src
                lightboxImg.alt = lightboxImages[currentLightboxIndex].alt
                gsap.to(lightboxImg, { opacity: 1, scale: 1, duration: 0.3 })
            }
        })
    }
}

if (lightbox) {
    document.querySelectorAll('.lightbox-trigger[data-lightbox-group]').forEach((item) => {
        item.addEventListener('click', (event) => {
            event.preventDefault()
            const groupName = item.dataset.lightboxGroup
            if (!groupName) return
            const groupItems = Array.from(document.querySelectorAll(`.lightbox-trigger[data-lightbox-group="${groupName}"]`))
            const itemIndex = groupItems.indexOf(item)
            if (itemIndex === -1) return
            openLightboxImage(groupName, itemIndex)
        })
    })

    videoPresentationTrigger?.addEventListener('click', () => {
        const videoId = videoPresentationTrigger.dataset.videoId
        if (videoId) openLightboxVideo(videoId)
    })

    lightboxClose?.addEventListener('click', closeLightbox)
    lightboxPrev?.addEventListener('click', () => showLightboxImage(currentLightboxIndex - 1))
    lightboxNext?.addEventListener('click', () => showLightboxImage(currentLightboxIndex + 1))

    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) closeLightbox()
    })

    // Keyboard nav
    document.addEventListener('keydown', (e) => {
        if (!lightbox.classList.contains('active')) return
        if (e.key === 'Escape') closeLightbox()
        if (lightbox.classList.contains('is-video')) return
        if (e.key === 'ArrowLeft') showLightboxImage(currentLightboxIndex - 1)
        if (e.key === 'ArrowRight') showLightboxImage(currentLightboxIndex + 1)
    })
}

// ============================================================
//  SMOOTH ANCHOR LINKS
// ============================================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const targetId = this.getAttribute('href')
        if (targetId && targetId !== '#') {
            const targetEl = document.querySelector(targetId)
            if (targetEl) {
                e.preventDefault()
                lenis.scrollTo(targetEl, { offset: -80, duration: 1.4 })
            }
        }
    })
})

// ============================================================
//  ADV CARDS — NUMBER HOVER EFFECT
// ============================================================
document.querySelectorAll('.adv-card').forEach((card, i) => {
    card.addEventListener('mouseenter', () => {
        gsap.to(card.querySelector('.adv-icon-wrap'), {
            rotation: 5, scale: 1.05, duration: 0.4, ease: 'power2.out'
        })
    })
    card.addEventListener('mouseleave', () => {
        gsap.to(card.querySelector('.adv-icon-wrap'), {
            rotation: 0, scale: 1, duration: 0.4, ease: 'power2.out'
        })
    })
})

// ============================================================
//  PLAN CARDS — GSAP hover enhancement
// ============================================================
document.querySelectorAll('.plan-card').forEach(card => {
    card.addEventListener('mouseenter', () => {
        gsap.to(card, { y: -8, duration: 0.4, ease: 'power2.out' })
    })
    card.addEventListener('mouseleave', () => {
        gsap.to(card, { y: 0, duration: 0.4, ease: 'power2.out' })
    })
})

// ============================================================
//  NUMBERS SECTION — STAGGER ANIMATION WHEN VISIBLE
// ============================================================
const numberItems = document.querySelectorAll('.number-item')
if (numberItems.length) {
    ScrollTrigger.create({
        trigger: '#numbers',
        start: 'top 75%',
        onEnter: () => {
            gsap.fromTo(numberItems,
                { opacity: 0, y: 30 },
                { opacity: 1, y: 0, duration: 0.8, stagger: 0.12, ease: 'power3.out' }
            )
        }
    })
}
