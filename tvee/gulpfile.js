var gulp = require('gulp');
var coffee = require('gulp-coffee');
var watch = require('gulp-watch');
var clean = require('gulp-clean');

var static_dir = './static/';
var coffee_dir = static_dir + 'coffee/';
var js_dir = static_dir + 'js/';

gulp.task('clean-js', function () {
    return gulp.src(js_dir + '*', {read: false})
               .pipe(clean());
});


gulp.task('coffee', ['clean-js'], function() {
    return gulp.src(coffee_dir + '*.coffee')
        .pipe(coffee({bare: true}))
        .pipe(gulp.dest(js_dir));
});


gulp.task('default', ['coffee']);


gulp.task('coffee-watch', function() {
    return gulp.src(coffee_dir + '*.coffee')
        .pipe(watch(coffee_dir + '*.coffee', function(files) {
            return files.pipe(coffee({bare: true}))
                        .pipe(gulp.dest(js_dir));
        }));
});


gulp.task('watch', ['coffee-watch']);
