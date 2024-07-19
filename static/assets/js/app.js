// 헤더 스크롤
window.addEventListener('scroll', function() {
    const header = document.getElementById('head');
    if (window.scrollY > 10) { // Adjust the scroll threshold as needed
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});


//다이어리 슬라이드
const slider = document.querySelector('.slider');
const nextButton = document.getElementById('next');
const prevButton = document.getElementById('prev');
let currentIndex = 0;
let accumulatedDistance = 0;

function getSlideDetails() {
    const slide = document.querySelector('.card');
    const slideWidth = slide.offsetWidth;
    const marginLeft = parseFloat(getComputedStyle(slide).marginLeft);
    return { slideWidth, marginLeft };
}

function updateSliderPosition() {
    const { slideWidth, marginLeft } = getSlideDetails();
    if (currentIndex === 0) {
        accumulatedDistance = 0;
    } else {
        accumulatedDistance = -((slideWidth + marginLeft) * (currentIndex - 1) + (slideWidth / 2 + marginLeft));
    }
    slider.style.transform = `translateX(${accumulatedDistance}px)`;
}

function updateButtons() {
    const slides = document.querySelectorAll('.card');
    nextButton.style.display = currentIndex === slides.length - 1 ? 'none' : 'flex';
    prevButton.style.display = currentIndex === 0 ? 'none' : 'flex';
}

nextButton.addEventListener('click', () => {
    const { slideWidth, marginLeft } = getSlideDetails();
    let moveDistance;
    if (currentIndex === 0) {
        moveDistance = (slideWidth / 2) + marginLeft;
    } else {
        moveDistance = slideWidth + marginLeft;
    }
    accumulatedDistance -= moveDistance;
    currentIndex++;
    slider.style.transform = `translateX(${accumulatedDistance}px)`;
    updateButtons();
});

prevButton.addEventListener('click', () => {
    if (currentIndex === 0) return;
    const { slideWidth, marginLeft } = getSlideDetails();
    let moveDistance;
    if (currentIndex === 1) {
        moveDistance = (slideWidth / 2) + marginLeft;
    } else {
        moveDistance = slideWidth + marginLeft;
    }
    accumulatedDistance += moveDistance;
    currentIndex--;
    slider.style.transform = `translateX(${accumulatedDistance}px)`;
    updateButtons();
});

// 초기 상태 버튼 업데이트
updateButtons();

// 창 크기 변경 이벤트 리스너 추가
window.addEventListener('resize', () => {
    updateSliderPosition();
    updateButtons();
});


// card 넓이
function adjustCardWidth() {
    const sliderContainer = document.querySelector('.slider-container');
    const cards = sliderContainer.querySelectorAll('.card');

    const containerWidth = sliderContainer.offsetWidth; // .slider-container의 너비 가져오기

    let cardWidth;

    // 화면 너비가 768px 이하인 경우
    if (window.innerWidth < 720) {
        cardWidth = `calc((${containerWidth}px * 0.66) - 1.5rem)`; // .66으로 계산
        cards.forEach(card => {
            card.style.maxWidth = 'none';
        });
    } else {
        cardWidth = `calc((${containerWidth}px * 0.4) - 1.5rem)`; // 기본값인 .4로 계산
        cards.forEach(card => {
            card.style.maxWidth = '300px';
        });
    }
    // 각 카드에 너비 설정
    cards.forEach(card => {
        card.style.width = cardWidth;
    });
}

// 페이지 로드 시 및 리사이즈 이벤트 시 호출
window.addEventListener('load', adjustCardWidth);
window.addEventListener('resize', adjustCardWidth);



