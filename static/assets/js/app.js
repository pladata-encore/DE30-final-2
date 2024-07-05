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
const slide = document.querySelector('.card');
const slideWidth = slide.offsetWidth;
const halfSlideWidth = slideWidth / 2;
const marginLeft = parseFloat(getComputedStyle(slide).marginLeft);
let currentIndex = 0;
let accumulatedDistance = 0; // 현재까지 누적된 이동 거리

// .slider 요소의 padding-left 값을 반의 넓이로 설정
slider.style.paddingLeft = `${halfSlideWidth}px`;

// transform: translateX() 값을 초기화하여 음수 값으로 설정
slider.style.transform = `translateX(-${halfSlideWidth}px)`;

function getMoveDistance() {
    return slideWidth + marginLeft;
}

function updateButtons() {
    const slides = document.querySelectorAll('.card');
    nextButton.style.display = currentIndex === slides.length - 1 ? 'none' : 'flex';
    prevButton.style.display = currentIndex === 0 ? 'none' : 'flex';
}

nextButton.addEventListener('click', () => {
    const moveDistance = getMoveDistance();
    accumulatedDistance -= moveDistance;

    slider.style.transform = `translateX(${accumulatedDistance}px)`;

    currentIndex++;
    updateButtons();
});

prevButton.addEventListener('click', () => {
    if (currentIndex === 0) return;

    const moveDistance = getMoveDistance();
    accumulatedDistance += moveDistance;

    slider.style.transform = `translateX(${accumulatedDistance}px)`;

    currentIndex--;
    updateButtons();

});

// 초기 상태 버튼 업데이트
updateButtons();

// 창 크기 변경 이벤트 리스너 추가
window.addEventListener('resize', () => {
    const moveDistance = getMoveDistance();
    accumulatedDistance = -moveDistance * currentIndex; // 이동 거리 재계산
    slider.style.transform = `translateX(${accumulatedDistance}px)`;
    updateButtons();
});